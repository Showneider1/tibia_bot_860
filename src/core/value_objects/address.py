from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryAddress:
    """Wrapper para endereços de memória (melhora type safety)."""
    value: int

    def __add__(self, other: int) -> "MemoryAddress":
        if not isinstance(other, int):
            return NotImplemented
        return MemoryAddress(self.value + other)

    def __radd__(self, other: int) -> "MemoryAddress":
        return self.__add__(other)

    def __sub__(self, other: int) -> "MemoryAddress":
        if not isinstance(other, int):
            return NotImplemented
        return MemoryAddress(self.value - other)

    def with_offset(self, offset: int) -> "MemoryAddress":
        return MemoryAddress(self.value + offset)
