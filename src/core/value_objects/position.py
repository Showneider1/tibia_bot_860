from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """Posição no mapa (x, y, z)."""
    x: int
    y: int
    z: int

    def distance_chebyshev(self, other: "Position") -> int:
        return max(abs(self.x - other.x), abs(self.y - other.y))

    def same_floor(self, other: "Position") -> bool:
        return self.z == other.z
