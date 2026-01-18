"""
Leitor de memória com cache inteligente.
"""
import ctypes
import time
from typing import Optional, Any
from src.core.interfaces.memory_interface import IMemoryReader
from src.core.value_objects.address import MemoryAddress
from src.core.exceptions.memory_exceptions import MemoryReadError


class MemoryCache:
    """Cache simples com TTL para leituras de memória."""

    def __init__(self, ttl: float = 0.1):
        self._cache: dict[int, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, address: MemoryAddress) -> Optional[Any]:
        """Busca valor no cache."""
        if address.value in self._cache:
            value, timestamp = self._cache[address.value]
            if time.time() - timestamp < self._ttl:
                return value
            else:
                del self._cache[address.value]
        return None

    def set(self, address: MemoryAddress, value: Any) -> None:
        """Armazena valor no cache."""
        self._cache[address.value] = (value, time.time())

    def clear(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()

    def invalidate(self, address: MemoryAddress) -> None:
        """Invalida endereço específico."""
        if address.value in self._cache:
            del self._cache[address.value]


class MemoryReader(IMemoryReader):
    """Implementação de leitura de memória usando Windows API."""

    def __init__(self, process_manager, cache_ttl: float = 0.1):
        self._pm = process_manager
        self._cache = MemoryCache(ttl=cache_ttl)

    def read_int(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Lê um inteiro de 4 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_int()
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise MemoryReadError(f"Falha ao ler inteiro em {address}")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_int64(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Lê um inteiro de 8 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_int64()
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise MemoryReadError(f"Falha ao ler int64 em {address}")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_byte(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Lê 1 byte (0-255)."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached & 0xFF

        buffer = ctypes.c_ubyte()
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise MemoryReadError(f"Falha ao ler byte em {address}")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_float(self, address: MemoryAddress, use_cache: bool = True) -> float:
        """Lê um float de 4 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_float()
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise MemoryReadError(f"Falha ao ler float em {address}")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_double(self, address: MemoryAddress, use_cache: bool = True) -> float:
        """Lê um double de 8 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_double()
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            ctypes.byref(buffer),
            ctypes.sizeof(buffer),
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != ctypes.sizeof(buffer):
            raise MemoryReadError(f"Falha ao ler double em {address}")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_string(
        self, address: MemoryAddress, max_length: int = 256, use_cache: bool = True
    ) -> str:
        """Lê uma string terminada em null."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.create_string_buffer(max_length)
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            buffer,
            max_length,
            ctypes.byref(bytes_read),
        )

        if not success:
            raise MemoryReadError(f"Falha ao ler string em {address}")

        try:
            value = buffer.value.decode("latin-1", errors="ignore")
        except:
            value = ""

        if use_cache:
            self._cache.set(address, value)

        return value

    def read_bytes(
        self, address: MemoryAddress, size: int, use_cache: bool = True
    ) -> bytes:
        """Lê N bytes brutos."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t()

        success = ctypes.windll.kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            buffer,
            size,
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != size:
            raise MemoryReadError(f"Falha ao ler {size} bytes em {address}")

        value = buffer.raw
        if use_cache:
            self._cache.set(address, value)

        return value

    def clear_cache(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()

    def invalidate_cache(self, address: MemoryAddress) -> None:
        """Invalida endereço específico no cache."""
        self._cache.invalidate(address)
