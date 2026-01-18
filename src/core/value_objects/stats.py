from dataclasses import dataclass


@dataclass
class Stats:
    """Status básicos de vida/mana."""
    health: int
    max_health: int
    mana: int
    max_mana: int
