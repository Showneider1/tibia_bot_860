"""
Leitor de memoria com cache inteligente.
"""
import ctypes
from ctypes import wintypes
import time
from typing import Optional, Any
from src.core.interfaces.memory_interface import IMemoryReader
from src.core.value_objects.address import MemoryAddress
from src.core.exceptions.memory_exceptions import MemoryReadError


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
kernel32.ReadProcessMemory.restype = wintypes.BOOL


class MemoryCache:
    """Cache simples com TTL para leituras de memoria."""

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
        """Invalida endereco especifico."""
        if address.value in self._cache:
            del self._cache[address.value]


class MemoryReader(IMemoryReader):
    """Implementacao de leitura de memoria usando Windows API."""

    def __init__(self, process_manager, cache_ttl: float = 0.1):
        self._pm = process_manager
        self._cache = MemoryCache(ttl=cache_ttl)

    def _check_handle(self) -> None:
        """Valida se o handle do processo esta disponivel."""
        handle = getattr(self._pm, "process_handle", None)
        if not handle:
            raise MemoryReadError(
                "Handle de processo invalido ou nulo. "
                "O processo do Tibia pode ter sido fechado ou nao foi anexado corretamente."
            )

    def _read_raw(self, address: MemoryAddress, buffer, size: int, label: str):
        """Executa a chamada ReadProcessMemory com verificacao de erro detalhada."""
        self._check_handle()

        bytes_read = ctypes.c_size_t(0)

        success = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            ctypes.byref(buffer) if not hasattr(buffer, "raw") else buffer,
            size,
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != size:
            err = ctypes.get_last_error()
            raise MemoryReadError(
                f"Falha ao ler {label} em {address} (WinError {err}, bytes_read={bytes_read.value}/{size})"
            )

    def read_int(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Le um inteiro de 4 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_int()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "inteiro")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_int64(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Le um inteiro de 8 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_int64()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "int64")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_byte(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Le 1 byte (0-255)."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached & 0xFF

        buffer = ctypes.c_ubyte()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "byte")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_float(self, address: MemoryAddress, use_cache: bool = True) -> float:
        """Le um float de 4 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_float()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "float")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_double(self, address: MemoryAddress, use_cache: bool = True) -> float:
        """Le um double de 8 bytes."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_double()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "double")

        value = buffer.value
        if use_cache:
            self._cache.set(address, value)

        return value

    def read_string(
        self, address: MemoryAddress, max_length: int = 256, use_cache: bool = True
    ) -> str:
        """Le uma string terminada em null."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.create_string_buffer(max_length)
        self._check_handle()

        bytes_read = ctypes.c_size_t(0)

        success = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            buffer,
            max_length,
            ctypes.byref(bytes_read),
        )

        if not success:
            err = ctypes.get_last_error()
            raise MemoryReadError(f"Falha ao ler string em {address} (WinError {err})")

        try:
            value = buffer.value.decode("latin-1", errors="ignore")
        except Exception:
            value = ""

        if use_cache:
            self._cache.set(address, value)

        return value

    def read_bytes(
        self, address: MemoryAddress, size: int, use_cache: bool = True
    ) -> bytes:
        """Le N bytes brutos."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.create_string_buffer(size)
        self._check_handle()

        bytes_read = ctypes.c_size_t(0)

        success = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(address.value),
            buffer,
            size,
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != size:
            err = ctypes.get_last_error()
            raise MemoryReadError(
                f"Falha ao ler {size} bytes em {address} (WinError {err}, bytes_read={bytes_read.value}/{size})"
            )

        value = buffer.raw
        if use_cache:
            self._cache.set(address, value)

        return value

    def clear_cache(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()

    def invalidate_cache(self, address: MemoryAddress) -> None:
        """Invalida endereco especifico no cache."""
        self._cache.invalidate(address)