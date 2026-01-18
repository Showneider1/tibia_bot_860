from typing import Dict, Any
from .base_condition import BaseCondition
from src.core.entities.player import Player


class PlayerHPBelowCondition(BaseCondition):
    """Condição: HP do player abaixo de X%."""

    def __init__(self, threshold: int):
        super().__init__(f"PlayerHP<{threshold}%")
        self.threshold = threshold

    def evaluate(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        if not player:
            return False
        return player.hp_percent() < self.threshold


class PlayerManaBelowCondition(BaseCondition):
    """Condição: Mana do player abaixo de X%."""

    def __init__(self, threshold: int):
        super().__init__(f"PlayerMana<{threshold}%")
        self.threshold = threshold

    def evaluate(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        if not player:
            return False
        return player.mana_percent() < self.threshold


class PlayerLevelAboveCondition(BaseCondition):
    """Condição: Level do player acima de X."""

    def __init__(self, level: int):
        super().__init__(f"PlayerLevel>{level}")
        self.level = level

    def evaluate(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        if not player:
            return False
        return player.level > self.level
