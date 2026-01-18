from dataclasses import dataclass


@dataclass
class PlayerDTO:
    """DTO para transferir dados do jogador para UI."""
    id: int
    name: str
    health: int
    health_max: int
    mana: int
    mana_max: int
    level: int
    experience: int
