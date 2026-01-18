from enum import Enum


class CombatMode(str, Enum):
    """Modo de seleção de alvo."""
    LOWEST_HP = "lowest_hp"
    CLOSEST = "closest"
    HIGHEST_THREAT = "highest_threat"
