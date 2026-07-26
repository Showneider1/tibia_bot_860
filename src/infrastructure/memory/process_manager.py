"""
Gerenciador do handle do processo Tibia/Kaldrox.
"""
import ctypes
from ctypes import wintypes
import psutil
from typing import Optional
from src.core.constants.addresses_860 import PROCESS_NAME


kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.OpenProcess.argtypes = [
    wintypes.DWORD,
    wintypes.BOOL,
    wintypes.DWORD,
]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL


PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_VM_OPERATION = 0x0008
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_ALL_ACCESS = 0x1F0FFF

PROCESS_RW_ACCESS = (
    PROCESS_VM_READ
    | PROCESS_VM_WRITE
    | PROCESS_VM_OPERATION
    | PROCESS_QUERY_INFORMATION
)


class ProcessManager:
    """Gerencia handle do processo Tibia/Kaldrox."""

    def __init__(self) -> None:
        self.process_handle: Optional[int] = None
        self.process_id: Optional[int] = None
        self.last_error: Optional[int] = None

    def attach(self) -> bool:
        """Localiza o processo pelo nome e abre um handle valido."""
        found_pid = None

        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if PROCESS_NAME.lower() in name:
                    found_pid = proc.info["pid"]
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if found_pid is None:
            print(f"[ProcessManager] Processo '{PROCESS_NAME}' nao encontrado. "
                  f"Verifique se o Tibia/Kaldrox esta aberto.")
            return False

        self.process_id = found_pid

        handle = kernel32.OpenProcess(PROCESS_RW_ACCESS, False, found_pid)

        if not handle:
            self.last_error = ctypes.get_last_error()
            print(f"[ProcessManager] OpenProcess falhou com PROCESS_RW_ACCESS "
                  f"(WinError {self.last_error}). Tentando PROCESS_ALL_ACCESS...")

            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, found_pid)

            if not handle:
                self.last_error = ctypes.get_last_error()
                print(f"[ProcessManager] OpenProcess falhou com PROCESS_ALL_ACCESS "
                      f"(WinError {self.last_error}). "
                      f"Verifique se o script esta rodando como Administrador "
                      f"ou se ha protecao anti-cheat bloqueando o acesso.")
                self.process_handle = None
                return False

        self.process_handle = handle
        self.last_error = None
        return True

    def is_running(self) -> bool:
        """Verifica se o processo anexado ainda esta ativo."""
        if self.process_handle is None or self.process_id is None:
            return False
        try:
            p = psutil.Process(self.process_id)
            return p.is_running()
        except psutil.NoSuchProcess:
            return False

    def ensure_attached(self) -> bool:
        """Garante que ha um handle valido, tentando reanexar se necessario."""
        if self.process_handle and self.is_running():
            return True
        return self.attach()

    def detach(self) -> None:
        """Fecha o handle atual, se existir."""
        if self.process_handle:
            kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.process_id = None