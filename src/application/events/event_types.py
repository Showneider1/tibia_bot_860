from enum import Enum


class EventType(str, Enum):
    """Tipos de eventos do bot."""
    PLAYER_HEALTH_LOW = "player_health_low"
    PLAYER_MANA_LOW = "player_mana_low"
    CREATURE_DETECTED = "creature_detected"
    CREATURE_KILLED = "creature_killed"
    LEVEL_UP = "level_up"
    CONNECTION_LOST = "connection_lost"
