"""
Entidade Waypoint para navegação.
"""
from dataclasses import dataclass
from src.core.value_objects.position import Position


@dataclass
class Waypoint:
    """Representa um ponto de navegação."""
    
    position: Position
    action: str = "walk"  # walk, wait, use_item, use_spell, etc
    label: str = ""
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
