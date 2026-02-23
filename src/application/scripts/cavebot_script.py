"""
Script de navegação automática com A* pathfinding.
"""
import time
import win32con
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

        # Usa pathfinding se habilitado, repassando o bot_engine para injetar teclas
        if self.config["use_pathfinding"]:
            return self._navigate_with_pathfinding(player, current_wp, bot_engine)
        
        # Detecta se está travado (fallback se não estiver usando pathfinding)
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

    def _navigate_with_pathfinding(self, player: Player, waypoint: Waypoint, bot_engine: Any) -> bool:
        """Navega usando A* e envia as teclas de movimento em background."""
        # Calcula path se não existe ou se o player saiu da rota
        if not self._current_path or player.position not in self._current_path:
            self._current_path = self._pathfinder.find_path(
                player.position,
                waypoint.position
            )
            
            if not self._current_path:
                self._log.warning("Pathfinding falhou! Rota bloqueada.")
                return False
            
            self._log.info(f"Path calculado: {len(self._current_path)} passos")
        
        # O A* retorna a lista de posições do início ao fim.
        # Encontra onde o player está na rota para pegar o próximo passo.
        try:
            current_index = self._current_path.index(player.position)
            if current_index + 1 < len(self._current_path):
                next_step = self._current_path[current_index + 1]
                
                # Calcula o Delta (diferença) entre X e Y para saber a direção
                dx = next_step.x - player.position.x
                dy = next_step.y - player.position.y
                
                vk_code = None
                
                # Mapeamento de Direção para Virtual Key Codes do Windows (Setas e Numpad)
                if dx == 1 and dy == 0:     # Leste
                    vk_code = win32con.VK_RIGHT
                elif dx == -1 and dy == 0:  # Oeste
                    vk_code = win32con.VK_LEFT
                elif dx == 0 and dy == -1:  # Norte
                    vk_code = win32con.VK_UP
                elif dx == 0 and dy == 1:   # Sul
                    vk_code = win32con.VK_DOWN
                elif dx == 1 and dy == -1:  # Nordeste (Numpad 9)
                    vk_code = win32con.VK_NUMPAD9
                elif dx == -1 and dy == -1: # Noroeste (Numpad 7)
                    vk_code = win32con.VK_NUMPAD7
                elif dx == 1 and dy == 1:   # Sudeste (Numpad 3)
                    vk_code = win32con.VK_NUMPAD3
                elif dx == -1 and dy == 1:  # Sudoeste (Numpad 1)
                    vk_code = win32con.VK_NUMPAD1

                if vk_code:
                    self._log.debug(f"Andando para X:{next_step.x} Y:{next_step.y}")
                    bot_engine._injector.send_key_background(vk_code)
                    
                    # Delay importantíssimo! Se enviar muito rápido, o Tibia dá 'exhausted' de passos.
                    # Você pode ajustar esse tempo depois de acordo com a velocidade (speed) do personagem.
                    time.sleep(0.4) 
                    return True

        except ValueError:
            # Player não está no current_path (foi empurrado, andou na mão, etc), reseta a rota
            self._current_path = []
            
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