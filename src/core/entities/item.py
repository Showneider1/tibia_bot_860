from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    """Item do jogo (para looter, backpacks, etc)."""
    id: int
    name: str
    stackable: bool = False
    weight: float = 0.0
