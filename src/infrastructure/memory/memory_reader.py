"""
Leitor de memoria com cache inteligente e bypass de ASLR.
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
    """Cache simples com TTL para leituras de memoria otimizado para alta performance."""
    def __init__(self, ttl: float = 0.1):
        self._cache: dict[int, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, address: MemoryAddress) -> Optional[Any]:
        if address.value in self._cache:
            value, timestamp = self._cache[address.value]
            if time.perf_counter() - timestamp < self._ttl:
                return value
            else:
                del self._cache[address.value]
        return None

    def set(self, address: MemoryAddress, value: Any) -> None:
        self._cache[address.value] = (value, time.perf_counter())

    def clear(self) -> None:
        self._cache.clear()

    def invalidate(self, address: MemoryAddress) -> None:
        if address.value in self._cache:
            del self._cache[address.value]


class MemoryReader(IMemoryReader):
    """Implementacao de leitura de memoria usando Windows API com injeção ASLR."""

    def __init__(self, process_manager, cache_ttl: float = 0.1):
        self._pm = process_manager
        self._cache = MemoryCache(ttl=cache_ttl)

    def _check_handle(self) -> None:
        """Valida se o handle do processo esta disponivel."""
        handle = getattr(self._pm, "process_handle", None)
        if not handle:
            raise MemoryReadError(
                "Handle de processo invalido ou nulo. O processo foi fechado?"
            )

    def _get_real_address(self, address: MemoryAddress) -> int:
        """Calcula o endereço real somando a diferença gerada pelo ASLR."""
        # Se a base real for 0x400000, o delta será 0 (Tibia Clássico)
        # Se a base for 0x7FF..., aplicará a correção perfeitamente.
        base = getattr(self._pm, "base_address", 0x400000)
        aslr_delta = base - 0x400000
        return address.value + aslr_delta

    def _read_raw(self, address: MemoryAddress, buffer, size: int, label: str):
        """Executa a chamada ReadProcessMemory aplicando ASLR de forma transparente."""
        self._check_handle()
        real_address = self._get_real_address(address)

        if real_address <= 0:
            raise MemoryReadError(f"Tentativa de leitura em ponteiro nulo ({label}).")

        bytes_read = ctypes.c_size_t(0)
        success = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(real_address),
            ctypes.byref(buffer) if not hasattr(buffer, "raw") else buffer,
            size,
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != size:
            err = ctypes.get_last_error()
            # Note a mudança na string de erro, agora mostrando o endereço Real.
            raise MemoryReadError(
                f"Falha ao ler {label} em {address} (Real: {hex(real_address)}) - (WinError {err})"
            )

    def read_int(self, address: MemoryAddress, use_cache: bool = True) -> int:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_int()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "inteiro")

        if use_cache:
            self._cache.set(address, buffer.value)
        return buffer.value

    def read_int64(self, address: MemoryAddress, use_cache: bool = True) -> int:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_int64()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "int64")

        if use_cache:
            self._cache.set(address, buffer.value)
        return buffer.value

    def read_byte(self, address: MemoryAddress, use_cache: bool = True) -> int:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached & 0xFF

        buffer = ctypes.c_ubyte()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "byte")

        if use_cache:
            self._cache.set(address, buffer.value)
        return buffer.value

    def read_float(self, address: MemoryAddress, use_cache: bool = True) -> float:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.c_float()
        self._read_raw(address, buffer, ctypes.sizeof(buffer), "float")

        if use_cache:
            self._cache.set(address, buffer.value)
        return buffer.value

    def read_string(self, address: MemoryAddress, max_length: int = 256, use_cache: bool = True) -> str:
        real_address = self._get_real_address(address)
        if real_address <= 0:
            return ""

        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.create_string_buffer(max_length)
        self._check_handle()
        bytes_read = ctypes.c_size_t(0)

        success = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(real_address),
            buffer,
            max_length,
            ctypes.byref(bytes_read),
        )

        if not success and bytes_read.value == 0:
            err = ctypes.get_last_error()
            raise MemoryReadError(f"Falha ao ler string em {address} (Real: {hex(real_address)}) - WinError {err}")

        try:
            raw_data = buffer.raw[:bytes_read.value]
            clean_bytes = raw_data.split(b'\x00', 1)[0]
            value = clean_bytes.decode("latin-1", errors="ignore")
        except Exception:
            value = ""

        if use_cache:
            self._cache.set(address, value)
        return value

    def read_bytes(self, address: MemoryAddress, size: int, use_cache: bool = True) -> bytes:
        real_address = self._get_real_address(address)
        if real_address <= 0:
            raise MemoryReadError("Tentativa de ler N bytes de um ponteiro nulo.")

        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        buffer = ctypes.create_string_buffer(size)
        self._check_handle()
        bytes_read = ctypes.c_size_t(0)

        success = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_void_p(real_address),
            buffer,
            size,
            ctypes.byref(bytes_read),
        )

        if not success or bytes_read.value != size:
            err = ctypes.get_last_error()
            raise MemoryReadError(
                f"Falha ao ler {size} bytes em {address} (Real: {hex(real_address)}) - (WinError {err})"
            )

        if use_cache:
            self._cache.set(address, buffer.raw)
        return buffer.raw

    def clear_cache(self) -> None:
        self._cache.clear()

    def invalidate_cache(self, address: MemoryAddress) -> None:
        self._cache.invalidate(address)