from dataclasses import dataclass
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats


@dataclass
class Creature:
    """Entidade de criatura (monstro/jogador) na battle list."""
    id: int
    name: str
    position: Position
    stats: Stats
    visible: bool
    walking: bool
    battle_slot: int = -1

    def is_alive(self) -> bool:
        return self.stats.health > 0
