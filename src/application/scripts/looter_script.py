import time
from typing import Dict, Any, Set
from .base_script import BaseScript
from src.core.entities.player import Player


class LooterScript(BaseScript):
    """Script de auto-loot."""

    def __init__(self):
        super().__init__("Looter")
        self.priority = 20
        self.config = {
            "enabled": False,
            "loot_radius": 1,  # SQMs ao redor
            "items_to_loot": {  # ID: nome
                3031: "Gold Coin",
                3035: "Platinum Coin",
            },
            "open_corpses": True,
            "loot_hotkey": "Shift+RightClick",  # Placeholder
        }
        self._looted_positions: Set[tuple] = set()

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        # TODO: Implementar detecção de corpses na memória
        # Por enquanto é placeholder
        
        self._log.debug("Looter ativo, mas sem corpses detectados.")
        return False

    def mark_looted(self, x: int, y: int, z: int) -> None:
        """Marca posição como já saqueada."""
        self._looted_positions.add((x, y, z))

    def clear_looted_cache(self) -> None:
        """Limpa cache de posições saqueadas."""
        self._looted_positions.clear()
