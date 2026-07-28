import ctypes
import ctypes.wintypes as wintypes
from src.core.interfaces.memory_interface import IMemoryWriter
from src.core.value_objects.address import MemoryAddress
from .process_manager import ProcessManager

# CORRECAO: argtypes com c_uint32 para LPCVOID
# Impede que Python 64-bit passe ponteiro de 8 bytes para processo 32-bit,
# eliminando WinError 299 (ERROR_PARTIAL_COPY).
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.WriteProcessMemory.argtypes = [
    wintypes.HANDLE,          # hProcess
    ctypes.c_uint32,          # lpBaseAddress — FORÇADO 32-bit
    ctypes.c_void_p,          # lpBuffer
    ctypes.c_size_t,          # nSize
    ctypes.POINTER(ctypes.c_size_t),  # lpNumberOfBytesWritten
]
kernel32.WriteProcessMemory.restype = wintypes.BOOL


class MemoryWriter(IMemoryWriter):
    """Escritor de memória usando WinAPI — compatível com processos 32-bit."""

    def __init__(self, process_manager: ProcessManager) -> None:
        self._pm = process_manager

    @property
    def _handle(self):
        return self._pm.process_handle

    def write_int(self, address: MemoryAddress, value: int) -> bool:
        data = int(value).to_bytes(4, "little", signed=False)
        bytes_written = ctypes.c_size_t(0)
        ok = kernel32.WriteProcessMemory(
            self._handle, ctypes.c_uint32(address.value), data, len(data), ctypes.byref(bytes_written)
        )
        return bool(ok and bytes_written.value == len(data))

    def write_bytes(self, address: MemoryAddress, data: bytes) -> bool:
        size = len(data)
        c_data = ctypes.create_string_buffer(data, size)
        bytes_written = ctypes.c_size_t(0)
        ok = kernel32.WriteProcessMemory(
            self._handle, ctypes.c_uint32(address.value), c_data, size, ctypes.byref(bytes_written)
        )
        return bool(ok and bytes_written.value == size)
