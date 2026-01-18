from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryAddress:
    """Wrapper para endereços de memória (melhora type safety)."""
    value: int

    def with_offset(self, offset: int) -> "MemoryAddress":
        return MemoryAddress(self.value + offset)
