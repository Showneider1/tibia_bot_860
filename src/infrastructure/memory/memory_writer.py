import ctypes
from src.core.interfaces.memory_interface import IMemoryWriter
from src.core.value_objects.address import MemoryAddress
from .process_manager import ProcessManager


class MemoryWriter(IMemoryWriter):
    """Escritor de memória usando WinAPI."""

    def __init__(self, process_manager: ProcessManager) -> None:
        self._pm = process_manager

    @property
    def _handle(self):
        return self._pm.process_handle

    def write_int(self, address: MemoryAddress, value: int) -> bool:
        data = int(value).to_bytes(4, "little", signed=False)
        bytes_written = ctypes.c_size_t(0)
        ok = ctypes.windll.kernel32.WriteProcessMemory(
            self._handle, address.value, data, len(data), ctypes.byref(bytes_written)
        )
        return bool(ok and bytes_written.value == len(data))

    def write_bytes(self, address: MemoryAddress, data: bytes) -> bool:
        size = len(data)
        c_data = ctypes.create_string_buffer(data, size)
        bytes_written = ctypes.c_size_t(0)
        ok = ctypes.windll.kernel32.WriteProcessMemory(
            self._handle, address.value, c_data, size, ctypes.byref(bytes_written)
        )
        return bool(ok and bytes_written.value == size)
