from dataclasses import dataclass


@dataclass(frozen=True)
class Spell:
    """Representação de spell (healing/attack/buff)."""
    name: str
    words: str
    mana_cost: int
    cooldown_ms: int
    min_level: int = 0
    min_magic_level: int = 0
