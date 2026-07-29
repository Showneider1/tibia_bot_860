"""
Script de navegacao automatica com A* pathfinding, follow system e anti-stuck.
Inspirado em ElfBot/XenoBot cavebot robusto.

Historico de correcoes:
  BUG-B: _navigate_with_pathfinding usava .index() que causava ValueError por jitter
         -> corrigido com _find_nearest_index() usando distancia Chebyshev
  BUG-C: max_distance_to_waypoint=1 nunca atingido por jitter -> aumentado para 2
  BUG-G: scripts acessavam bot_engine._injector -> corrigido para bot_engine.injector
  BUG-STUCK: _last_move_time=0 causava anti-stuck no primeiro tick
  BUG-INDEX: _current_waypoint_index nao resetado ao reativar
  BUG-POS: posicao (0,0,0) devia ser ignorada (memoria nao sincronizada)
  BUG-SLEEP: time.sleep(step_delay) dentro de execute() bloqueava o script_engine
             inteiro, impedindo healing/buff de rodar durante o walk.
             Corrigido com cooldown baseado em timestamp (_last_step_time).
  BUG-SENDINPUT: send_key_background + win32con falha com WinError 87 em contextos
             sem desktop interativo e nao funciona em background.
             Corrigido no KeyboardInjector v4: SendInput -> PostMessage.
  BUG-WALKTO: _move_player chamava walk_to(next_step) com apenas 1 argumento.
             memory_walker.walk_to exige (current, destination).
             Com 1 arg: current=next_step, destination ausente -> TypeError ou
             dx=0,dy=0 -> sem movimento apesar do log indicar andando.
             Corrigido: walk_to(current_pos, next_step).
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
            "max_distance_to_waypoint": 2,
            "use_pathfinding": True,

            # step_delay: intervalo minimo entre passos (segundos).
            "step_delay": 0.35,

            # Anti-stuck
            "enable_anti_stuck": True,
            "stuck_timeout": 2.0,
            "stuck_retries": 5,

            # Follow
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
        self._pending_move_position: Optional[Position] = None
        self._pending_move_time: float = 0.0
        self._last_move_time = 0.0
        self._last_step_time = 0.0
        self._wait_until = 0.0
        self._pathfinder = Pathfinder()
        self._current_path: List[Position] = []
        self._follow_target: Optional[Creature] = None
        self._last_follow_position: Optional[Position] = None
        self._blocked_tiles: set = set()

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def on_enable(self) -> None:
        now = time.time()
        self._last_move_time  = now
        self._last_step_time  = 0.0
        self._current_waypoint_index = 0
        self._current_path    = []
        self._stuck_counter   = 0
        self._wait_until      = 0.0
        self._last_position   = None
        self._pending_move_position = None
        self._pending_move_time = 0.0
        self._follow_target   = None
        self._last_follow_position = None
        self._blocked_tiles.clear()
        self._log.info("CaveBot ativado - contadores resetados.")

    def on_disable(self) -> None:
        self._current_path  = []
        self._follow_target = None
        self._log.info("CaveBot desativado.")

    # ------------------------------------------------------------------
    # Execucao principal
    # ------------------------------------------------------------------

    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Chamado a cada tick pelo ScriptEngine.
        Cooldown entre passos via _last_step_time (sem time.sleep).
        Movimento via MemoryWalker (PostMessage WM_KEYDOWN/WM_KEYUP).
        """
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        # Verifica walker disponivel
        walker = getattr(bot_engine, "walker", None)
        if walker is None:
            self._log.error("bot_engine.walker nao disponivel!")
            return False

        # Cooldown entre passos
        if not walker.cooldown_passed(self.config["step_delay"]):
            return False

        if self.config["enable_follow"]:
            return self._execute_follow(player, creatures, bot_engine)

        return self._execute_waypoints(player, creatures, bot_engine)

    # ------------------------------------------------------------------
    # Modo Follow
    # ------------------------------------------------------------------

    def _execute_follow(
        self, player: Player, creatures: List[Creature], bot_engine: Any
    ) -> bool:
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
        if (
            self._last_follow_position
            and target_pos.distance_chebyshev(self._last_follow_position) < 1
        ):
            return False

        self._last_follow_position = target_pos
        distance = player.position.distance_chebyshev(target_pos)

        if distance <= self.config["follow_distance"]:
            return False

        if distance > self.config["follow_max_distance"]:
            self._log.warning(
                f"Follow target muito longe ({distance} sqm), recalculando..."
            )

        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(
                player, target_pos, bot_engine, target_is_creature=True
            )
        return self._move_towards(player, target_pos, bot_engine)

    # ------------------------------------------------------------------
    # Modo Waypoint
    # ------------------------------------------------------------------

    def _execute_waypoints(
        self, player: Player, creatures: List[Creature], bot_engine: Any
    ) -> bool:
        waypoints: List[Waypoint] = self.config.get("waypoints", [])
        if not waypoints:
            return False

        if player.position.x <= 0 or player.position.y <= 0:
            self._log.debug("Posicao invalida (0,0,0), aguardando sincronizacao...")
            return False

        # Aguardando ação "wait" completar
        if time.time() < self._wait_until:
            return False

        if self._current_waypoint_index >= len(waypoints):
            self._current_waypoint_index = 0
            self._current_path = []
            self._log.debug("Indice fora do limite, voltando ao waypoint 0.")

        current_wp = waypoints[self._current_waypoint_index]
        distance   = player.position.distance_chebyshev(current_wp.position)

        if distance <= self.config["max_distance_to_waypoint"]:
            self._log.info(
                f"Waypoint {self._current_waypoint_index} alcancado! "
                f"({current_wp.position.x},{current_wp.position.y},{current_wp.position.z})"
            )
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
                self._log.warning("Caminho perigoso, aguardando...")
                return False

        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(
                player, current_wp.position, bot_engine
            )

        return self._move_towards(player, current_wp.position, bot_engine)

    # ------------------------------------------------------------------
    # Navegacao com A*
    # ------------------------------------------------------------------

    def _find_nearest_index(self, player_pos: Position) -> int:
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
        target_is_creature: bool = False,
    ) -> bool:
        needs_recalc = (
            not self._current_path
            or self._find_nearest_index(player.position) == -1
            or (target_is_creature and self._path_needs_recalc(player, target_pos))
        )

        if needs_recalc:
            self._current_path = self._pathfinder.find_path(
                player.position, target_pos
            )
            if not self._current_path:
                self._log.warning("Pathfinding falhou! Movimento direto...")
                return self._move_towards(player, target_pos, bot_engine)
            self._log.info(
                f"Path: {len(self._current_path)} passos ate "
                f"({target_pos.x},{target_pos.y},{target_pos.z})"
            )

        current_index = self._find_nearest_index(player.position)
        if current_index == -1:
            self._current_path = []
            return False

        next_index = current_index + 1
        if next_index < len(self._current_path):
            return self._move_player(
                player.position, self._current_path[next_index], bot_engine
            )

        self._current_path = []
        return False

    def _path_needs_recalc(self, player: Player, target_pos: Position) -> bool:
        if not self._current_path:
            return True
        return self._current_path[-1].distance_chebyshev(target_pos) > 2

    # ------------------------------------------------------------------
    # Movimento via MemoryWalker (PostMessage WM_KEYDOWN/WM_KEYUP)
    # BUG-WALKTO FIX: walk_to requer (current, destination) - dois argumentos.
    # ------------------------------------------------------------------

    def _move_player(
        self, current_pos: Position, next_step: Position, bot_engine: Any
    ) -> bool:
        """
        Envia um passo via bot_engine.walker.walk_to(current_pos, next_step).

        CORRECAO BUG-WALKTO:
          Antes: walk_to(next_step)          <- 1 argumento, dx=0/dy=0, sem movimento
          Agora: walk_to(current_pos, next_step) <- correto, direcao calculada ok
        """
        self._log.debug(
            f"Andando: ({current_pos.x},{current_pos.y}) -> "
            f"({next_step.x},{next_step.y})"
        )
        ok = bot_engine.walker.walk_to(current_pos, next_step)
        if ok:
            self._last_move_time = time.time()
            self._last_step_time = time.time()
            self._pending_move_position = next_step
            self._pending_move_time = time.time()
        return ok

    def _move_towards(
        self, player: Player, target: Position, bot_engine: Any
    ) -> bool:
        """
        Movimento direto (sem pathfinding):
        calcula o proximo tile na direcao do alvo e envia via MemoryWalker.
        Se o tile direto estiver bloqueado, tenta as outras direcoes ortogonais
        em ordem de preferencia (mais proximo do alvo primeiro).
        """
        if not player.position:
            return False
        dx = max(-1, min(1, target.x - player.position.x))
        dy = max(-1, min(1, target.y - player.position.y))
        if dx == 0 and dy == 0:
            return False

        # Tenta a direcao preferencial primeiro; se bloqueada, tenta as outras
        candidates = [(dx, dy)]
        for odx, ody in [(dx, 0), (0, dy), (-dx, 0), (0, -dy), (-dx, -dy)]:
            cand = (odx, ody)
            if cand != (dx, dy) and cand != (0, 0) and cand not in candidates:
                candidates.append(cand)
        # Filtra candidatos redundantes e (0,0)
        seen = set()
        unique = []
        for c in candidates:
            if c != (0, 0) and c not in seen:
                seen.add(c)
                unique.append(c)

        for cdx, cdy in unique:
            next_step = Position(
                player.position.x + cdx,
                player.position.y + cdy,
                player.position.z,
            )
            next_key = (next_step.x, next_step.y, next_step.z)
            if next_key in self._blocked_tiles:
                continue
            return self._move_player(player.position, next_step, bot_engine)

        # Todas bloqueadas — tenta a direcao original mesmo sabendo que pode falhar
        next_step = Position(
            player.position.x + dx,
            player.position.y + dy,
            player.position.z,
        )
        return self._move_player(player.position, next_step, bot_engine)

    # ------------------------------------------------------------------
    # Anti-stuck
    # ------------------------------------------------------------------

    def _is_stuck(self, player: Player) -> bool:
        if time.time() - self._last_move_time < self.config["stuck_timeout"]:
            return False

        if self._pending_move_position and player.position == self._pending_move_position:
            self._pending_move_position = None
            self._pending_move_time = 0.0
            self._last_position = player.position
            self._stuck_counter = 0
            self._blocked_tiles.clear()
            return False

        if self._pending_move_position and time.time() - self._pending_move_time > 0.6:
            key = (self._pending_move_position.x, self._pending_move_position.y, self._pending_move_position.z)
            self._blocked_tiles.add(key)
            self._log.warning(
                f"Tile bloqueado ({self._pending_move_position.x},{self._pending_move_position.y})! "
                f"{self._stuck_counter+1}/{self.config['stuck_retries']}"
            )
            self._pending_move_position = None
            self._pending_move_time = 0.0
            self._stuck_counter += 1
            return True

        if self._last_position and self._last_position == player.position:
            self._stuck_counter += 1
            self._log.warning(
                f"Stuck detectado! {self._stuck_counter}/{self.config['stuck_retries']}"
            )
            return True
        self._last_position = player.position
        self._stuck_counter = 0
        return False

    def _handle_stuck(self) -> None:
        self._pending_move_position = None
        self._pending_move_time = 0.0
        if self._stuck_counter >= self.config["stuck_retries"]:
            self._log.warning("Stuck prolongado! Pulando waypoint...")
            self._next_waypoint(len(self.config.get("waypoints", [])))
            self._stuck_counter = 0
            self._current_path  = []
        else:
            self._current_path   = []
            self._last_move_time = time.time()

    # ------------------------------------------------------------------
    # Perigos
    # ------------------------------------------------------------------

    def _is_path_dangerous(
        self, player: Player, target: Position, creatures: List[Creature]
    ) -> bool:
        dangerous = self.config.get("dangerous_creatures", [])
        if not dangerous:
            return False
        for creature in creatures:
            if creature.name in dangerous:
                if (
                    player.position.distance_chebyshev(creature.position) <= 5
                    and target.distance_chebyshev(creature.position) <= 5
                ):
                    return True
        return False

    # ------------------------------------------------------------------
    # Acoes de waypoint
    # ------------------------------------------------------------------

    def _execute_waypoint_action(
        self, waypoint: Waypoint, bot_engine: Any
    ) -> None:
        if not hasattr(waypoint, "action") or not waypoint.action:
            return
        action = waypoint.action.lower()
        meta = waypoint.metadata or {}

        if action == "deposit":
            self._log.info("Depositando items no depot...")
        elif action == "refuel":
            self._log.info("Reabastecendo supplies...")
        elif action == "wait":
            duration = meta.get("wait_time", 2)
            self._log.info(f"Aguardando no waypoint ({duration}s)...")
            self._wait_until = time.time() + duration
        elif action.startswith("say:"):
            msg = action.split(":", 1)[1]
            bot_engine.injector.say(msg)
            self._log.info(f"Dizendo: {msg}")

        elif action == "rope":
            hotkey = meta.get("hotkey", self.config.get("rope_hotkey", "F2"))
            self._log.info(f"Usando corda (hotkey {hotkey})...")
            bot_engine.injector.send_hotkey(hotkey)
            self._wait_until = time.time() + 1.5

        elif action == "shovel":
            hotkey = meta.get("hotkey", self.config.get("shovel_hotkey", "F3"))
            self._log.info(f"Usando pa (hotkey {hotkey})...")
            bot_engine.injector.send_hotkey(hotkey)
            self._wait_until = time.time() + 1.5

        elif action == "ladder":
            direction = meta.get("direction", "up")
            self._log.info(f"Usando escada ({direction})...")
            if direction == "up":
                bot_engine.injector.send_key_background(win32con.VK_UP)
            else:
                bot_engine.injector.send_key_background(win32con.VK_DOWN)
            self._wait_until = time.time() + 1.0

        elif action == "use":
            hotkey = meta.get("hotkey", self.config.get("use_hotkey", "F4"))
            self._log.info(f"Usando item (hotkey {hotkey})...")
            bot_engine.injector.send_hotkey(hotkey)
            self._wait_until = time.time() + 2.0

        elif action == "lure":
            wait = meta.get("wait_time", 3)
            self._log.info(f"Lure ativo: aguardando {wait}s para as criaturas...")
            self._wait_until = time.time() + wait

    # ------------------------------------------------------------------
    # Controle de indice
    # ------------------------------------------------------------------

    def _next_waypoint(self, total: int) -> None:
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
        self.config["waypoints"].append(waypoint)

    def clear_waypoints(self) -> None:
        self.config["waypoints"] = []
        self._current_waypoint_index = 0
        self._current_path = []
        self._blocked_tiles.clear()

    def start_follow(self, target_name: str, distance: int = 2) -> None:
        self.config["enable_follow"] = True
        self.config["follow_target_name"] = target_name
        self.config["follow_distance"] = distance
        self._follow_target = None
        self._log.info(f"Follow iniciado: {target_name}")

    def stop_follow(self) -> None:
        self.config["enable_follow"] = False
        self.config["follow_target_name"] = ""
        self._follow_target = None
        self._log.info("Follow parado.")

    def get_status(self) -> Dict:
        return {
            "enabled":          self.enabled,
            "current_waypoint": self._current_waypoint_index,
            "total_waypoints":  len(self.config.get("waypoints", [])),
            "follow_mode":      self.config["enable_follow"],
            "follow_target":    self.config.get("follow_target_name", ""),
            "stuck_count":      self._stuck_counter,
            "last_step_ago_ms": int((time.time() - self._last_step_time) * 1000),
        }
