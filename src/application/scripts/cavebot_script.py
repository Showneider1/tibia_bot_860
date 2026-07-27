"""
Script de navegacao automatica com A* pathfinding, follow system e anti-stuck.
Inspirado em ElfBot/XenoBot cavebot robusto.

BUG-B CORRIGIDO: _navigate_with_pathfinding() nao mais usa
  'player.position not in self._current_path' nem '.index()'.
  Posicao lida da memoria tem jitter de +-1 sqm e raramente coincide
  exatamente com no do path, causando reset do path a cada tick e
  impedindo qualquer avanco. Novo _find_nearest_index() usa distancia
  Chebyshev (tolerancia <= 1 sqm) para localizar no mais proximo.

BUG-C CORRIGIDO: max_distance_to_waypoint aumentado de 1 para 2.
  Tolerancia 1 nunca era atingida por jitter de posicao.
  Valor 2 e padrao seguro para Tibia 8.60. Configuravel.

BUG-G CORRIGIDO: _move_player() e _move_towards() usam
  bot_engine.injector (property publica) ao inves de
  bot_engine._injector (atributo privado).

BUG-STUCK CORRIGIDO: _last_move_time=0 fazia anti-stuck disparar
  imediatamente no primeiro tick (time.time()-0 >> stuck_timeout).
  on_enable() agora inicializa _last_move_time = time.time().

BUG-INDEX CORRIGIDO: _current_waypoint_index nao era resetado ao
  reativar o cavebot. on_enable() agora reseta indice, path e contadores.

BUG-POS CORRIGIDO: _execute_waypoints agora valida se player.position
  e valida (x>0, y>0) antes de calcular distancia. Posicao (0,0,0) indica
  que a leitura de memoria ainda nao sincronizou; o tick e pulado.
"""
import time
import win32con
from typing import Dict, Any, List, Optional
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position
from src.ai.pathfinding.pathfinder import Pathfinder


class CavebotScript(BaseScript):
    """Script de navegacao automatica com pathfinding, follow e anti-stuck."""

    def __init__(self):
        super().__init__("CaveBot")
        self.priority = 30
        self.config = {
            "waypoints": [],
            "loop": True,
            # BUG-C FIX: era 1, aumentado para 2 para absorver jitter de leitura
            "max_distance_to_waypoint": 2,
            "use_pathfinding": True,

            # Anti-stuck system
            "enable_anti_stuck": True,
            "stuck_timeout": 8.0,
            "stuck_retries": 3,
            "step_delay": 0.4,

            # Follow system
            "enable_follow": False,
            "follow_target_name": "",
            "follow_distance": 2,
            "follow_max_distance": 8,
            "pause_follow_in_combat": True,

            # Anti-danger
            "avoid_dangerous_creatures": False,
            "dangerous_creatures": ["Dragon Lord", "Demon", "Warlock"],
        }
        self._current_waypoint_index = 0
        self._stuck_counter = 0
        self._last_position: Optional[Position] = None
        # BUG-STUCK FIX: inicializado com time.time() no on_enable(),
        # nao com 0. Valor 0 faz time.time()-0 >> stuck_timeout no 1o tick.
        self._last_move_time = 0.0
        self._pathfinder = Pathfinder()
        self._current_path: List[Position] = []
        self._follow_target: Optional[Creature] = None
        self._last_follow_position: Optional[Position] = None

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def on_enable(self) -> None:
        """
        BUG-STUCK FIX: inicializa _last_move_time com o tempo atual.
        BUG-INDEX FIX: reseta indice, path e contadores ao ativar.

        Sem esses resets:
          1. anti-stuck dispara no primeiro tick (time.time()-0 >> 8s)
          2. indice pode apontar alem do fim da lista se o usuario
             desativou/reativou o cavebot com waypoints diferentes.
        """
        self._last_move_time = time.time()
        self._current_waypoint_index = 0
        self._current_path = []
        self._stuck_counter = 0
        self._last_position = None
        self._follow_target = None
        self._last_follow_position = None
        self._log.info("CaveBot ativado — contadores resetados.")

    def on_disable(self) -> None:
        """Limpa estado ao desativar."""
        self._current_path = []
        self._follow_target = None
        self._log.info("CaveBot desativado.")

    # ------------------------------------------------------------------
    # Execucao principal
    # ------------------------------------------------------------------

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        if self.config["enable_follow"]:
            return self._execute_follow(player, creatures, bot_engine)

        return self._execute_waypoints(player, creatures, bot_engine)

    # ------------------------------------------------------------------
    # Modo Follow
    # ------------------------------------------------------------------

    def _execute_follow(self, player: Player, creatures: List[Creature], bot_engine) -> bool:
        """Executa modo follow (seguir um player)."""
        target_name = self.config["follow_target_name"]
        if not target_name:
            return False

        if not self._follow_target or self._follow_target.name != target_name:
            self._follow_target = None
            for creature in creatures:
                if creature.name == target_name:
                    self._follow_target = creature
                    break

            if not self._follow_target:
                self._log.warning(f"Follow target nao encontrado: {target_name}")
                return False

        target_pos = self._follow_target.position
        if (self._last_follow_position and
                target_pos.distance_chebyshev(self._last_follow_position) < 1):
            return False

        self._last_follow_position = target_pos
        distance = player.position.distance_chebyshev(target_pos)

        if distance <= self.config["follow_distance"]:
            return False

        if distance > self.config["follow_max_distance"]:
            self._log.warning(f"Follow target muito longe ({distance} sqm), recalculando...")

        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(
                player, target_pos, bot_engine, target_is_creature=True
            )
        return self._move_towards(player, target_pos, bot_engine)

    # ------------------------------------------------------------------
    # Modo Waypoint
    # ------------------------------------------------------------------

    def _execute_waypoints(self, player: Player, creatures: List[Creature], bot_engine) -> bool:
        """Executa navegacao por waypoints."""
        waypoints: List[Waypoint] = self.config.get("waypoints", [])
        if not waypoints:
            return False

        # BUG-POS FIX: valida posicao do player antes de qualquer calculo.
        # Posicao (0,0,0) indica que a leitura de memoria ainda nao sincronizou
        # (PlayerReader retornou fallback ou BattleList nao achou o player ainda).
        # Pular o tick e mais seguro do que calcular distancia errada.
        if player.position.x <= 0 or player.position.y <= 0:
            self._log.debug("CaveBot: posicao do player invalida (0,0,0), aguardando sincronizacao...")
            return False

        # BUG-INDEX FIX: garante que o indice esta dentro dos limites.
        # Pode ficar fora dos limites se waypoints foram modificados enquanto
        # o cavebot estava ativo.
        if self._current_waypoint_index >= len(waypoints):
            self._current_waypoint_index = 0
            self._current_path = []
            self._log.debug("CaveBot: indice fora do limite, voltando ao waypoint 0.")

        current_wp = waypoints[self._current_waypoint_index]
        distance = player.position.distance_chebyshev(current_wp.position)

        # BUG-C FIX: tolerancia 2 sqm (era 1)
        if distance <= self.config["max_distance_to_waypoint"]:
            self._log.info(f"Waypoint {self._current_waypoint_index} alcancado! ({current_wp.position.x},{current_wp.position.y},{current_wp.position.z})")
            self._execute_waypoint_action(current_wp, bot_engine)
            self._next_waypoint(len(waypoints))
            self._current_path = []
            return True

        if self.config["enable_anti_stuck"]:
            if self._is_stuck(player):
                self._handle_stuck()
                return False

        if self.config["avoid_dangerous_creatures"]:
            if self._is_path_dangerous(player, current_wp.position, creatures):
                self._log.warning("Caminho bloqueado por criatura perigosa, esperando...")
                return False

        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(player, current_wp.position, bot_engine)

        return self._move_towards(player, current_wp.position, bot_engine)

    # ------------------------------------------------------------------
    # Navegacao com A*
    # ------------------------------------------------------------------

    def _find_nearest_index(self, player_pos: Position) -> int:
        """
        BUG-B FIX: substitui 'self._current_path.index(player.position)'.

        Localiza o indice do no do path mais proximo da posicao atual
        usando distancia Chebyshev. Tolerancia de 1 sqm para absorver
        o jitter da leitura de memoria do Tibia.

        Returns:
            Indice do no mais proximo, ou -1 se todos estiverem > 1 sqm.
        """
        best_idx  = -1
        best_dist = 9999
        for i, pos in enumerate(self._current_path):
            d = player_pos.distance_chebyshev(pos)
            if d < best_dist:
                best_dist = d
                best_idx  = i
        return best_idx if best_dist <= 1 else -1

    def _navigate_with_pathfinding(
        self,
        player: Player,
        target_pos: Position,
        bot_engine: Any,
        target_is_creature: bool = False
    ) -> bool:
        """
        Navega usando A* e envia as teclas de movimento em background.

        BUG-B FIX:
          ANTES (quebrado):
            if player.position not in self._current_path:  # sempre True por jitter
                recalcula path
            current_index = self._current_path.index(player.position)  # ValueError

          AGORA (correto):
            Usa _find_nearest_index() com tolerancia Chebyshev <= 1 sqm.
            Path so e recalculado se:
              1. Nao ha path ativo
              2. Player saiu da tolerancia de todos os nos
              3. Alvo se moveu (modo follow)
        """
        needs_recalc = (
            not self._current_path
            or self._find_nearest_index(player.position) == -1
            or (target_is_creature and self._path_needs_recalc(player, target_pos))
        )

        if needs_recalc:
            self._current_path = self._pathfinder.find_path(
                player.position,
                target_pos
            )
            if not self._current_path:
                self._log.warning("Pathfinding falhou! Tentando movimento direto...")
                return self._move_towards(player, target_pos, bot_engine)
            self._log.info(f"Path calculado: {len(self._current_path)} passos ate ({target_pos.x},{target_pos.y},{target_pos.z})")

        current_index = self._find_nearest_index(player.position)
        if current_index == -1:
            self._current_path = []
            return False

        next_index = current_index + 1
        if next_index < len(self._current_path):
            next_step = self._current_path[next_index]
            return self._move_player(player.position, next_step, bot_engine)

        self._current_path = []
        return False

    def _path_needs_recalc(self, player: Player, target_pos: Position) -> bool:
        """Verifica se o path precisa ser recalculado (target se moveu)."""
        if not self._current_path:
            return True
        last_pos = self._current_path[-1]
        return last_pos.distance_chebyshev(target_pos) > 2

    # ------------------------------------------------------------------
    # Movimento
    # BUG-G FIX: usa bot_engine.injector (property publica)
    #            ao inves de bot_engine._injector (atributo privado)
    # ------------------------------------------------------------------

    def _move_player(self, current_pos: Position, next_step: Position, bot_engine: Any) -> bool:
        """Move player de current_pos para next_step enviando tecla apropriada."""
        dx = next_step.x - current_pos.x
        dy = next_step.y - current_pos.y

        vk_code = self._direction_to_key(dx, dy)
        if vk_code:
            self._log.debug(f"Andando: ({current_pos.x},{current_pos.y}) -> ({next_step.x},{next_step.y}) dx={dx} dy={dy}")
            bot_engine.injector.send_key_background(vk_code)
            self._last_move_time = time.time()
            time.sleep(self.config["step_delay"])
            return True
        self._log.warning(f"Direcao invalida: dx={dx} dy={dy}")
        return False

    def _move_towards(self, player: Player, target: Position, bot_engine: Any) -> bool:
        """Movimento direto sem pathfinding (fallback)."""
        dx = max(-1, min(1, target.x - player.position.x))
        dy = max(-1, min(1, target.y - player.position.y))

        if dx == 0 and dy == 0:
            return False

        vk_code = self._direction_to_key(dx, dy)
        if vk_code:
            self._log.debug(f"Movimento direto: dx={dx} dy={dy} -> ({target.x},{target.y})")
            bot_engine.injector.send_key_background(vk_code)
            self._last_move_time = time.time()
            time.sleep(self.config["step_delay"])
            return True
        return False

    def _direction_to_key(self, dx: int, dy: int) -> Optional[int]:
        """Converte direcao (dx, dy) em virtual key code."""
        if   dx ==  1 and dy ==  0: return win32con.VK_RIGHT
        elif dx == -1 and dy ==  0: return win32con.VK_LEFT
        elif dx ==  0 and dy == -1: return win32con.VK_UP
        elif dx ==  0 and dy ==  1: return win32con.VK_DOWN
        elif dx ==  1 and dy == -1: return win32con.VK_NUMPAD9
        elif dx == -1 and dy == -1: return win32con.VK_NUMPAD7
        elif dx ==  1 and dy ==  1: return win32con.VK_NUMPAD3
        elif dx == -1 and dy ==  1: return win32con.VK_NUMPAD1
        return None

    # ------------------------------------------------------------------
    # Anti-stuck
    # ------------------------------------------------------------------

    def _is_stuck(self, player: Player) -> bool:
        """Detecta se o player esta stuck (nao esta se movendo)."""
        # BUG-STUCK FIX: _last_move_time e inicializado com time.time() no
        # on_enable(), entao essa condicao so dispara apos stuck_timeout
        # segundos SEM nenhum movimento — comportamento correto.
        if time.time() - self._last_move_time < self.config["stuck_timeout"]:
            return False

        if self._last_position and self._last_position == player.position:
            self._stuck_counter += 1
            self._log.warning(
                f"Stuck detectado! Tentativa {self._stuck_counter}/{self.config['stuck_retries']}"
            )
            return True

        self._last_position = player.position
        self._stuck_counter = 0
        return False

    def _handle_stuck(self) -> None:
        """Lida com situacao de stuck."""
        if self._stuck_counter >= self.config["stuck_retries"]:
            self._log.warning("Player stuck por muito tempo! Pulando waypoint...")
            self._next_waypoint(len(self.config.get("waypoints", [])))
            self._stuck_counter = 0
            self._current_path = []
        else:
            self._current_path = []
            self._last_move_time = time.time()

    # ------------------------------------------------------------------
    # Perigos
    # ------------------------------------------------------------------

    def _is_path_dangerous(
        self, player: Player, target: Position, creatures: List[Creature]
    ) -> bool:
        """Verifica se ha criaturas perigosas no caminho."""
        dangerous = self.config.get("dangerous_creatures", [])
        if not dangerous:
            return False

        for creature in creatures:
            if creature.name in dangerous:
                dist_to_player = player.position.distance_chebyshev(creature.position)
                dist_to_target = target.distance_chebyshev(creature.position)
                if dist_to_player <= 5 and dist_to_target <= 5:
                    return True
        return False

    # ------------------------------------------------------------------
    # Acoes de waypoint
    # ------------------------------------------------------------------

    def _execute_waypoint_action(self, waypoint: Waypoint, bot_engine: Any) -> None:
        """Executa acao associada a um waypoint."""
        if not hasattr(waypoint, "action") or not waypoint.action:
            return
        action = waypoint.action.lower()

        if action == "deposit":
            self._log.info("Depositando items no depot...")
        elif action == "refuel":
            self._log.info("Reabastecendo supplies...")
        elif action == "wait":
            self._log.info("Aguardando no waypoint...")
            time.sleep(2)
        elif action.startswith("say:"):
            msg = action.split(":", 1)[1]
            bot_engine.injector.cast_spell(msg)
            self._log.info(f"Dizendo: {msg}")

    # ------------------------------------------------------------------
    # Controle de indice
    # ------------------------------------------------------------------

    def _next_waypoint(self, total: int) -> None:
        """Avanca para proximo waypoint."""
        self._current_waypoint_index += 1
        if self._current_waypoint_index >= total:
            if self.config["loop"]:
                self._current_waypoint_index = 0
                self._log.info("Loop: voltando ao inicio.")
            else:
                self._current_waypoint_index = total - 1
                self._log.info("Cavebot finalizado.")

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def add_waypoint(self, waypoint: Waypoint) -> None:
        """Adiciona waypoint a rota."""
        self.config["waypoints"].append(waypoint)

    def clear_waypoints(self) -> None:
        """Limpa todos os waypoints."""
        self.config["waypoints"] = []
        self._current_waypoint_index = 0
        self._current_path = []

    def start_follow(self, target_name: str, distance: int = 2) -> None:
        """Inicia modo follow."""
        self.config["enable_follow"] = True
        self.config["follow_target_name"] = target_name
        self.config["follow_distance"] = distance
        self._follow_target = None
        self._log.info(f"Follow iniciado para: {target_name}")

    def stop_follow(self) -> None:
        """Para modo follow."""
        self.config["enable_follow"] = False
        self.config["follow_target_name"] = ""
        self._follow_target = None
        self._log.info("Follow parado.")

    def get_status(self) -> Dict:
        """Retorna status atual do cavebot."""
        return {
            "enabled": self.enabled,
            "current_waypoint": self._current_waypoint_index,
            "total_waypoints": len(self.config.get("waypoints", [])),
            "in_combat_pause": self.config.get("pause_follow_in_combat", False),
            "follow_mode": self.config["enable_follow"],
            "follow_target": self.config.get("follow_target_name", ""),
            "stuck_count": self._stuck_counter,
        }
