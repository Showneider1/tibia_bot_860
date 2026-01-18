"""
Script de navegação automática com A* pathfinding.
"""
import time
from typing import Dict, Any, List
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position
from src.ai.pathfinding.pathfinder import Pathfinder


class CavebotScript(BaseScript):
    """Script de navegação automática com pathfinding."""

    def __init__(self):
        super().__init__("CaveBot")
        self.priority = 30
        self.config = {
            "enabled": False,
            "waypoints": [],
            "loop": True,
            "max_distance_to_waypoint": 1,
            "use_pathfinding": True,
        }
        self._current_waypoint_index = 0
        self._stuck_counter = 0
        self._last_position: Position | None = None
        self._pathfinder = Pathfinder()
        self._current_path: List[Position] = []

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        waypoints: List[Waypoint] = self.config.get("waypoints", [])
        if not waypoints:
            return False

        current_wp = waypoints[self._current_waypoint_index]
        distance = player.position.distance_chebyshev(current_wp.position)

        # Chegou no waypoint?
        if distance <= self.config["max_distance_to_waypoint"]:
            self._log.info(f"✓ Waypoint {self._current_waypoint_index} alcançado!")
            self._next_waypoint(len(waypoints))
            self._current_path = []
            return True

        # Usa pathfinding se habilitado
        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(player, current_wp)
        
        # Detecta se está travado
        if self._last_position and self._last_position == player.position:
            self._stuck_counter += 1
            if self._stuck_counter > 10:
                self._log.warning("Player travado! Pulando waypoint...")
                self._next_waypoint(len(waypoints))
                self._stuck_counter = 0
        else:
            self._stuck_counter = 0

        self._last_position = player.position
        
        self._log.debug(
            f"Navegando para waypoint {self._current_waypoint_index}: "
            f"{current_wp.position} (dist: {distance})"
        )
        
        return False

    def _navigate_with_pathfinding(self, player: Player, waypoint: Waypoint) -> bool:
        """Navega usando A*."""
        # Calcula path se não existe
        if not self._current_path:
            self._current_path = self._pathfinder.find_path(
                player.position,
                waypoint.position
            )
            
            if not self._current_path:
                self._log.warning("Pathfinding falhou! Indo direto...")
                return False
            
            self._log.info(f"Path calculado: {len(self._current_path)} passos")
        
        # Pega próximo passo
        if len(self._current_path) > 1:
            next_step = self._current_path[1]
            self._log.debug(f"Próximo passo: {next_step}")
            
            # TODO: Implementar movimento real (click, WASD, etc)
            # Por enquanto só loga
            
        return False

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

    def add_waypoint(self, waypoint: Waypoint) -> None:
        """Adiciona waypoint à rota."""
        self.config["waypoints"].append(waypoint)

    def clear_waypoints(self) -> None:
        """Limpa todos os waypoints."""
        self.config["waypoints"] = []
        self._current_waypoint_index = 0
        self._current_path = []
