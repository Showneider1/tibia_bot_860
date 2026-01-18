from abc import ABC, abstractmethod
from typing import List
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.entities.waypoint import Waypoint


class IAIProvider(ABC):
    """Contrato para qualquer motor de IA que plugarmos depois."""

    @abstractmethod
    def select_optimal_target(self, player: Player, creatures: List[Creature]) -> Creature | None:
        ...

    @abstractmethod
    def compute_best_path(self, start: Waypoint, goal: Waypoint) -> List[Waypoint]:
        ...

    @abstractmethod
    def suggest_healing_strategy(self, player: Player) -> str:
        ...
