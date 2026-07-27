"""
Script de navegacao automatica com A* pathfinding, follow system e anti-stuck.
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
    """Script de navegacao automatica com pathfinding, follow e anti-stuck."""

    def __init__(self):
        super().__init__("CaveBot")
        self.priority = 30
        self.config = {
            "waypoints": [],
            "loop": True,
            "max_distance_to_waypoint": 1,
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
        self._last_move_time = 0
        self._pathfinder = Pathfinder()
        self._current_path: List[Position] = []
        self._follow_target: Optional[Creature] = None
        self._last_follow_position: Optional[Position] = None

    def execute(self, context: Dict[str, Any]) -> bool:
        # BUG 2 CORRIGIDO: removida checagem de self.config["enabled"] que nunca
        # era setado. O controle de ativacao e feito via self.enabled (BaseScript),
        # que o ScriptEngine ja checa antes de chamar execute().
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
        follow_distance = self.config["follow_distance"]

        if distance <= follow_distance:
            return False

        if distance > self.config["follow_max_distance"]:
            self._log.warning(f"Follow target muito longe ({distance} sqm), recalculando...")

        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(player, target_pos, bot_engine,
                                                   target_is_creature=True)
        return self._move_towards(player, target_pos, bot_engine)

    def _execute_waypoints(self, player: Player, creatures: List[Creature], bot_engine) -> bool:
        """Executa navegacao por waypoints."""
        waypoints: List[Waypoint] = self.config.get("waypoints", [])
        if not waypoints:
            return False

        current_wp = waypoints[self._current_waypoint_index]
        distance = player.position.distance_chebyshev(current_wp.position)

        if distance <= self.config["max_distance_to_waypoint"]:
            self._log.info(f"Waypoint {self._current_waypoint_index} alcancado!")
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

    def _navigate_with_pathfinding(self, player: Player, target_pos: Position,
                                   bot_engine: Any, target_is_creature: bool = False) -> bool:
        """Navega usando A* e envia as teclas de movimento em background."""
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

        try:
            current_index = self._current_path.index(player.position)
            if current_index + 1 < len(self._current_path):
                next_step = self._current_path[current_index + 1]
                return self._move_player(player.position, next_step, bot_engine)
        except ValueError:
            self._current_path = []

        return False

    def _path_needs_recalc(self, player: Player, target_pos: Position) -> bool:
        """Verifica se o path precisa ser recalculado (target se moveu)."""
        if not self._current_path:
            return True
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

    def _is_stuck(self, player: Player) -> bool:
        """Detecta se o player esta stuck (nao esta se movendo)."""
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
        """Lida com situacao de stuck."""
        if self._stuck_counter >= self.config["stuck_retries"]:
            self._log.warning("Player stuck por muito tempo! Pulando waypoint...")
            self._next_waypoint(len(self.config.get("waypoints", [])))
            self._stuck_counter = 0
            self._current_path = []
        else:
            self._current_path = []
            self._last_move_time = time.time()

    def _is_path_dangerous(self, player: Player, target: Position,
                           creatures: List[Creature]) -> bool:
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

    def _execute_waypoint_action(self, waypoint: Waypoint, bot_engine: Any) -> None:
        """Executa acao associada a um waypoint."""
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
        """Avanca para proximo waypoint."""
        self._current_waypoint_index += 1
        if self._current_waypoint_index >= total:
            if self.config["loop"]:
                self._current_waypoint_index = 0
                self._log.info("Loop: voltando ao inicio.")
            else:
                self._current_waypoint_index = total - 1
                self._log.info("Cavebot finalizado.")

    # === API publica ===

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
