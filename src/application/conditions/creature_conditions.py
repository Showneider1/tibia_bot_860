from typing import Dict, Any, List
from .base_condition import BaseCondition
from src.core.entities.player import Player
from src.core.entities.creature import Creature


class CreatureNearbyCondition(BaseCondition):
    """Condição: Existe criatura próxima."""

    def __init__(self, max_distance: int = 7):
        super().__init__(f"CreatureNearby<{max_distance}")
        self.max_distance = max_distance

    def evaluate(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        
        if not player or not creatures:
            return False

        for creature in creatures:
            if player.position.distance_chebyshev(creature.position) <= self.max_distance:
                return True
        
        return False


class CreatureNameCondition(BaseCondition):
    """Condição: Existe criatura com nome específico."""

    def __init__(self, creature_name: str):
        super().__init__(f"Creature={creature_name}")
        self.creature_name = creature_name

    def evaluate(self, context: Dict[str, Any]) -> bool:
        creatures: List[Creature] = context.get("creatures", [])
        
        for creature in creatures:
            if self.creature_name.lower() in creature.name.lower():
                return True
        
        return False
