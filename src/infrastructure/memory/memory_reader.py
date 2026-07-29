"""
Leitor de memoria com cache inteligente.
Compatível com processo 32-bit lido por Python 64-bit.
"""
import ctypes
import ctypes.wintypes as wintypes
import struct
import time
from typing import Optional, Any

from src.core.interfaces.memory_interface import IMemoryReader
from src.core.value_objects.address import MemoryAddress
from src.core.exceptions.memory_exceptions import MemoryReadError

# CORREÇÃO DEFINITIVA: argtypes com c_uint32 para LPCVOID
# Impede que Python 64-bit passe ponteiro de 8 bytes para processo 32-bit,
# eliminando WinError 299 (ERROR_PARTIAL_COPY).
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.ReadProcessMemory.argtypes = [
    wintypes.HANDLE,          # hProcess
    ctypes.c_uint32,          # lpBaseAddress — FORÇADO 32-bit
    ctypes.c_void_p,          # lpBuffer
    ctypes.c_size_t,          # nSize
    ctypes.POINTER(ctypes.c_size_t),  # lpNumberOfBytesRead
]
kernel32.ReadProcessMemory.restype = wintypes.BOOL


class MemoryCache:
    """Cache simples com TTL."""
    def __init__(self, ttl: float = 0.1):
        self._cache: dict[int, tuple[Any, float]] = {}
        self._ttl = ttl

    def get(self, address: MemoryAddress) -> Optional[Any]:
        entry = self._cache.get(address.value)
        if entry:
            value, ts = entry
            if time.perf_counter() - ts < self._ttl:
                return value
            del self._cache[address.value]
        return None

    def set(self, address: MemoryAddress, value: Any) -> None:
        self._cache[address.value] = (value, time.perf_counter())

    def clear(self) -> None:
        self._cache.clear()

    def invalidate(self, address: MemoryAddress) -> None:
        self._cache.pop(address.value, None)


class MemoryReader(IMemoryReader):
    """Leitura de memória via Windows API — compatível com processos 32-bit."""

    def __init__(self, process_manager, cache_ttl: float = 0.1):
        self._pm = process_manager
        self._cache = MemoryCache(ttl=cache_ttl)

    def _check_handle(self) -> None:
        handle = getattr(self._pm, "process_handle", None)
        if not handle:
            raise MemoryReadError("Handle de processo inválido. O processo foi fechado?")

    def _get_real_address(self, address: MemoryAddress) -> int:
        # Tibia 8.60 / Kaldrox: endereços absolutos estáticos, sem delta ASLR
        return address.value

    def _read_bytes_raw(self, address: MemoryAddress, size: int, label: str) -> bytes:
        """
        Núcleo da leitura. Retorna `size` bytes brutos do processo alvo.

        Usa c_uint32 para o endereço (compatibilidade 32-bit processo / 64-bit Python).
        Buffer alocado via create_string_buffer — ponteiro estável para RPM.
        """
        self._check_handle()
        real_address = self._get_real_address(address)

        if real_address <= 0:
            raise MemoryReadError(f"Ponteiro nulo ao ler {label}.")

        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)

        ok = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_uint32(real_address),   # endereço truncado a 32-bit
            buf,
            ctypes.c_size_t(size),
            ctypes.byref(bytes_read),
        )

        if not ok or bytes_read.value != size:
            err = ctypes.get_last_error()
            raise MemoryReadError(
                f"Falha ao ler {label} em {address} "
                f"(Real: {hex(real_address)}) - (WinError {err})"
            )

        return buf.raw

    # ------------------------------------------------------------------
    # Leituras tipadas
    # ------------------------------------------------------------------

    def read_int(self, address: MemoryAddress, use_cache: bool = True) -> int:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached
        raw = self._read_bytes_raw(address, 4, "inteiro")
        value = struct.unpack_from("<i", raw)[0]
        if use_cache:
            self._cache.set(address, value)
        return value

    def read_uint(self, address: MemoryAddress, use_cache: bool = True) -> int:
        """Unsigned 32-bit — útil para IDs de criaturas."""
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached
        raw = self._read_bytes_raw(address, 4, "uint")
        value = struct.unpack_from("<I", raw)[0]
        if use_cache:
            self._cache.set(address, value)
        return value

    def read_int64(self, address: MemoryAddress, use_cache: bool = True) -> int:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached
        raw = self._read_bytes_raw(address, 8, "int64")
        value = struct.unpack_from("<q", raw)[0]
        if use_cache:
            self._cache.set(address, value)
        return value

    def read_byte(self, address: MemoryAddress, use_cache: bool = True) -> int:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached & 0xFF
        raw = self._read_bytes_raw(address, 1, "byte")
        value = struct.unpack_from("<B", raw)[0]
        if use_cache:
            self._cache.set(address, value)
        return value

    def read_float(self, address: MemoryAddress, use_cache: bool = True) -> float:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached
        raw = self._read_bytes_raw(address, 4, "float")
        value = struct.unpack_from("<f", raw)[0]
        if use_cache:
            self._cache.set(address, value)
        return value

    def read_string(self, address: MemoryAddress, max_length: int = 256, use_cache: bool = True) -> str:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached

        real_address = self._get_real_address(address)
        if real_address <= 0:
            return ""

        self._check_handle()
        buf = ctypes.create_string_buffer(max_length)
        bytes_read = ctypes.c_size_t(0)

        ok = kernel32.ReadProcessMemory(
            self._pm.process_handle,
            ctypes.c_uint32(real_address),
            buf,
            ctypes.c_size_t(max_length),
            ctypes.byref(bytes_read),
        )

        if not ok:
            err = ctypes.get_last_error()
            raise MemoryReadError(
                f"Falha ao ler string em {address} "
                f"(Real: {hex(real_address)}) - WinError {err}"
            )

        try:
            raw_data = buf.raw[: bytes_read.value]
            value = raw_data.split(b"\x00", 1)[0].decode("latin-1", errors="ignore")
        except Exception:
            value = ""

        if use_cache:
            self._cache.set(address, value)
        return value

    def read_bytes(self, address: MemoryAddress, size: int, use_cache: bool = True) -> bytes:
        if use_cache:
            cached = self._cache.get(address)
            if cached is not None:
                return cached
        raw = self._read_bytes_raw(address, size, f"{size} bytes")
        if use_cache:
            self._cache.set(address, raw)
        return raw

    def clear_cache(self) -> None:
        self._cache.clear()

    def invalidate_cache(self, address: MemoryAddress) -> None:
        self._cache.invalidate(address)
