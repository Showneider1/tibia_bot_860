from dataclasses import dataclass
from typing import Optional
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats


@dataclass
class Player:
    """Entidade principal do jogador no Tibia 8.60."""
    id: int
    name: str
    position: Position
    stats: Stats

    level: int
    experience: int
    magic_level: int
    soul: int
    stamina: int
    capacity: int
    vocation: str = "None"  # ADICIONADO

    def hp_percent(self) -> float:
        if self.stats.max_health <= 0:
            return 0.0
        return (self.stats.health / self.stats.max_health) * 100

    def mana_percent(self) -> float:
        if self.stats.max_mana <= 0:
            return 0.0
        return (self.stats.mana / self.stats.max_mana) * 100

    def is_alive(self) -> bool:
        return self.stats.health > 0
