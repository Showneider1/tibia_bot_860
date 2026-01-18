from dataclasses import dataclass


@dataclass
class CreatureDTO:
    """DTO para criatura."""
    id: int
    name: str
    health: int
    x: int
    y: int
    z: int
    visible: bool
