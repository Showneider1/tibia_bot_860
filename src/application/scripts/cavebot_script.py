"""
Script de navegação automática com A* pathfinding, follow system e anti-stuck.
Inspirado em ElfBot/XenoBot cavebot robusto.
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
    """Script de navegação automática com pathfinding, follow e anti-stuck."""

    def __init__(self):
        super().__init__("CaveBot")
        self.priority = 30
        self.config = {
            "enabled": False,
            "waypoints": [],
            "loop": True,
            "max_distance_to_waypoint": 1,
            "use_pathfinding": True,
            
            # Anti-stuck system
            "enable_anti_stuck": True,
            "stuck_timeout": 8.0,           # Segundos sem mover antes de considerar stuck
            "stuck_retries": 3,             # Tentativas antes de pular waypoint
            "step_delay": 0.4,              # Delay entre passos ((segundos)
            
            # Follow system
            "enable_follow": False,         # Seguir um player
            "follow_target_name": "",       # Nome do player para seguir
            "follow_distance": 2,           # Distância ideal ao seguir
            "follow_max_distance": 8,       # Distância máxima antes de recalcular
            "pause_follow_in_combat": True, # Pausar follow durante combate
            
            # Anti-danger
            "avoid_dangerous_creatures": False, # Desviar de criaturas perigosas no caminho
            "dangerous_creatures": ["Dragon Lord", "Demon", "Warlock"],
        }
        self._current_waypoint_index = 0
        self._stuck_counter = 0
        self._last_position: Optional[Position] = None
        self._last_move_time = 0
        self._pathfinder = Pathfinder()
        self._current_path: List[Position] = []
        self._follow_target: Optional[Creature] = None
        self._last_follow_position: Optional[Position] = None

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        # Modo follow tem prioridade sobre waypoints
        if self.config["enable_follow"]:
            return self._execute_follow(player, creatures, bot_engine)

        # Modo waypoint normal
        return self._execute_waypoints(player, creatures, bot_engine)

    def _execute_follow(self, player: Player, creatures: List[Creature], bot_engine) -> bool:
        """Executa modo follow (seguir um player)."""
        target_name = self.config["follow_target_name"]
        if not target_name:
            return False

        # Encontra target nas criaturas
        if not self._follow_target or self._follow_target.name != target_name:
            self._follow_target = None
            for creature in creatures:
                if creature.name == target_name:
                    self._follow_target = creature
                    break
            
            if not self._follow_target:
                self._log.warning(f"Follow target não encontrado: {target_name}")
                return False

        # Verifica se target mudou de posição significativamente
        target_pos = self._follow_target.position
        if (self._last_follow_position and 
            target_pos.distance_chebyshev(self._last_follow_position) < 1):
            # Target quase parado, não precisa mover
            return False

        self._last_follow_position = target_pos

        # Calcula distância
        distance = player.position.distance_chebyshev(target_pos)
        follow_distance = self.config["follow_distance"]

        if distance <= follow_distance:
            return False  # Já está perto o suficiente

        if distance > self.config["follow_max_distance"]:
            self._log.warning(f"Follow target muito longe ({distance} sqm), recalculando...")

        # Usa pathfinding para navegar até target
        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(player, target_pos, bot_engine, 
                                                     target_is_creature=True)
        else:
            # Movimento direto (sem pathfinding)
            return self._move_towards(player, target_pos, bot_engine)

    def _execute_waypoints(self, player: Player, creatures: List[Creature], bot_engine) -> bool:
        """Executa navegação por waypoints."""
        waypoints: List[Waypoint] = self.config.get("waypoints", [])
        if not waypoints:
            return False

        current_wp = waypoints[self._current_waypoint_index]
        distance = player.position.distance_chebyshev(current_wp.position)

        # Chegou no waypoint?
        if distance <= self.config["max_distance_to_waypoint"]:
            self._log.info(f"✓ Waypoint {self._current_waypoint_index} alcançado!")
            
            # Executa ação do waypoint se definida
            self._execute_waypoint_action(current_wp, bot_engine)
            
            self._next_waypoint(len(waypoints))
            self._current_path = []
            return True

        # Anti-stuck detection
        if self.config["enable_anti_stuck"]:
            if self._is_stuck(player):
                self._handle_stuck()
                return False

        # Evitar criaturas perigosas no caminho
        if self.config["avoid_dangerous_creatures"]:
            if self._is_path_dangerous(player, current_wp.position, creatures):
                self._log.warning("Caminho bloqueado por criatura perigosa, esperando...")
                return False

        # Usa pathfinding se habilitado
        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(player, current_wp.position, bot_engine)
        
        # Movimento direto (fallback)
        return self._move_towards(player, current_wp.position, bot_engine)

    def _navigate_with_pathfinding(self, player: Player, target_pos: Position, 
                                    bot_engine: Any, target_is_creature: bool = False) -> bool:
        """Navega usando A* e envia as teclas de movimento em background."""
        # Calcula path se não existe ou se o player saiu da rota
        if (not self._current_path or 
            player.position not in self._current_path or
            (target_is_creature and self._path_needs_recalc(player, target_pos))):
            self._current_path = self._pathfinder.find_path(
                player.position,
                target_pos
            )
            
            if not self._current_path:
                self._log.warning("Pathfinding falhou! Rota bloqueada.")
                return False
            
            self._log.info(f"Path calculado: {len(self._current_path)} passos")

        # Encontra onde o player está na rota
        try:
            current_index = self._current_path.index(player.position)
            if current_index + 1 < len(self._current_path):
                next_step = self._current_path[current_index + 1]
                return self._move_player(player.position, next_step, bot_engine)
        except ValueError:
            # Player não está no current_path, reseta a rota
            self._current_path = []
            
        return False

    def _path_needs_recalc(self, player: Player, target_pos: Position) -> bool:
        """Verifica se o path precisa ser recalculado (target se moveu)."""
        if not self._current_path:
            return True
        # Se target se moveu significativamente, recalcular
        last_pos = self._current_path[-1]
        return last_pos.distance_chebyshev(target_pos) > 2

    def _move_player(self, current_pos: Position, next_step: Position, bot_engine: Any) -> bool:
        """Move player de current_pos para next_step enviando tecla apropriada."""
        dx = next_step.x - current_pos.x
        dy = next_step.y - current_pos.y
        
        vk_code = self._direction_to_key(dx, dy)
        
        if vk_code:
            self._log.debug(f"Andando para X:{next_step.x} Y:{next_step.y}")
            bot_engine._injector.send_key_background(vk_code)
            self._last_move_time = time.time()
            time.sleep(self.config["step_delay"])
            return True
        
        return False

    def _move_towards(self, player: Player, target: Position, bot_engine: Any) -> bool:
        """Movimento direto sem pathfinding (fallback)."""
        dx = target.x - player.position.x
        dy = target.y - player.position.y
        
        # Normaliza para 1 SQM
        dx = max(-1, min(1, dx))
        dy = max(-1, min(1, dy))
        
        if dx == 0 and dy == 0:
            return False
        
        vk_code = self._direction_to_key(dx, dy)
        if vk_code:
            bot_engine._injector.send_key_background(vk_code)
            self._last_move_time = time.time()
            time.sleep(self.config["step_delay"])
            return True
        
        return False

    def _direction_to_key(self, dx: int, dy: int) -> Optional[int]:
        """Converte direção (dx, dy) em virtual key code."""
        if dx == 1 and dy == 0:       # Leste
            return win32con.VK_RIGHT
        elif dx == -1 and dy == 0:   # Oeste
            return win32con.VK_LEFT
        elif dx == 0 and dy == -1:    # Norte
            return win32con.VK_UP
        elif dx == 0 and dy == 1:     # Sul
            return win32con.VK_DOWN
        elif dx == 1 and dy == -1:    # Nordeste (Numpad 9)
            return win32con.VK_NUMPAD9
        elif dx == -1 and dy == -1:  # Noroeste (Numpad 7)
            return win32con.VK_NUMPAD7
        elif dx == 1 and dy == 1:     # Sudeste (Numpad 3)
            return win32con.VK_NUMPAD3
        elif dx == -1 and dy == 1:   # Sudoeste (Numpad 1)
            return win32con.VK_NUMPAD1
        return None

    def _is_stuck(self, player: Player) -> bool:
        """Detecta se o player está stuck (não está se movendo)."""
        if time.time() - self._last_move_time < self.config["stuck_timeout"]:
            return False
        
        if self._last_position and self._last_position == player.position:
            self._stuck_counter += 1
            self._log.warning(f"Stuck detectado! Tentativa {self._stuck_counter}/{self.config['stuck_retries']}")
            return True
        
        self._last_position = player.position
        self._stuck_counter = 0
        return False

    def _handle_stuck(self) -> None:
        """Lida com situação de stuck."""
        if self._stuck_counter >= self.config["stuck_retries"]:
            self._log.warning("Player stuck por muito tempo! Pulando waypoint...")
            self._next_waypoint(len(self.config.get("waypoints", [])))
            self._stuck_counter = 0
            self._current_path = []
        else:
            # Tenta recalcular path
            self._current_path = []
            self._last_move_time = time.time()

    def _is_path_dangerous(self, player: Player, target: Position, 
                           creatures: List[Creature]) -> bool:
        """Verifica se há criaturas perigosas no caminho."""
        dangerous = self.config.get("dangerous_creatures", [])
        if not dangerous:
            return False
        
        for creature in creatures:
            if creature.name in dangerous:
                # Verifica se criatura está entre player e target
                # (simplificação: verifica se está ближе que 3 SQMs da linha reta)
                dist_to_player = player.position.distance_chebyshev(creature.position)
                dist_to_target = target.distance_chebyshev(creature.position)
                
                if dist_to_player <= 5 and dist_to_target <= 5:
                    return True
        
        return False

    def _execute_waypoint_action(self, waypoint: Waypoint, bot_engine: Any) -> None:
        """Executa ação associada a um waypoint."""
        if hasattr(waypoint, "action") and waypoint.action:
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
                bot_engine._injector.cast_spell(msg)
                self._log.info(f"Dizendo: {msg}")

    def _next_waypoint(self, total: int) -> None:
        """Avança para próximo waypoint."""
        self._current_waypoint_index += 1
        if self._current_waypoint_index >= total:
            if self.config["loop"]:
                self._current_waypoint_index = 0
                self._log.info("🔄 Loop: voltando ao início.")
            else:
                self._current_waypoint_index = total - 1
                self._log.info("✓ Cavebot finalizado.")

    # === API pública ===

    def add_waypoint(self, waypoint: Waypoint) -> None:
        """Adiciona waypoint à rota."""
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
            "enabled": self.config["enabled"],
            "current_waypoint": self._current_waypoint_index,
            "total_waypoints": len(self.config.get("waypoints", [])),
            "in_combat_pause": self.config.get("pause_follow_in_combat", False),
            "follow_mode": self.config["enable_follow"],
            "follow_target": self.config.get("follow_target_name", ""),
            "stuck_count": self._stuck_counter,
        }