from abc import ABC, abstractmethod
from src.core.value_objects.address import MemoryAddress


class IMemoryReader(ABC):
    """Contrato para leitura de memória do cliente Tibia."""

    @abstractmethod
    def read_int(self, address: MemoryAddress, use_cache: bool = True) -> int:
        ...

    @abstractmethod
    def read_int64(self, address: MemoryAddress) -> int:
        ...

    @abstractmethod
    def read_string(self, address: MemoryAddress, length: int = 32) -> str:
        ...

    @abstractmethod
    def read_bytes(self, address: MemoryAddress, length: int) -> bytes:
        ...


class IMemoryWriter(ABC):
    """Contrato para escrita de memória."""

    @abstractmethod
    def write_int(self, address: MemoryAddress, value: int) -> bool:
        ...

    @abstractmethod
    def write_bytes(self, address: MemoryAddress, data: bytes) -> bool:
        ...
