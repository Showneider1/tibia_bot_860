import ctypes
import psutil
from typing import Optional
from src.core.constants.addresses_860 import PROCESS_NAME


PROCESS_ALL_ACCESS = 0x1F0FFF


class ProcessManager:
    """Gerencia handle do processo Tibia/Kaldrox."""

    def __init__(self) -> None:
        self.process_handle: Optional[int] = None
        self.process_id: Optional[int] = None

    def attach(self) -> bool:
        """Abre o processo e guarda o handle."""
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if PROCESS_NAME.lower() in (proc.info["name"] or "").lower():
                    self.process_id = proc.info["pid"]
                    handle = ctypes.windll.kernel32.OpenProcess(
                        PROCESS_ALL_ACCESS, False, self.process_id
                    )
                    if handle:
                        self.process_handle = handle
                        return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return False

    def is_running(self) -> bool:
        if self.process_handle is None or self.process_id is None:
            return False
        try:
            p = psutil.Process(self.process_id)
            return p.is_running()
        except psutil.NoSuchProcess:
            return False

    def detach(self) -> None:
        if self.process_handle:
            ctypes.windll.kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.process_id = None
