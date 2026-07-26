"""
Gerenciador do handle do processo Tibia/Kaldrox com suporte a ASLR.
"""
import ctypes
from ctypes import wintypes
import psutil
from typing import Optional

from src.core.constants.addresses_860 import PROCESS_NAME
from src.infrastructure.logging.logger import get_logger

# --- Configurações Win32 API (Kernel32) ---
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

# --- Configurações Win32 API (Psapi) para ASLR Bypass ---
psapi = ctypes.WinDLL("psapi", use_last_error=True)
LIST_MODULES_ALL = 0x03

psapi.EnumProcessModulesEx.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(wintypes.HMODULE),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.DWORD
]
psapi.EnumProcessModulesEx.restype = wintypes.BOOL

# --- Constantes de Privilégio ---
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
    """Gerencia handle do processo Tibia/Kaldrox e resolve Base Address."""

    def __init__(self) -> None:
        self._log = get_logger("ProcessManager")
        self.process_handle: Optional[int] = None
        self.process_id: Optional[int] = None
        self.last_error: Optional[int] = None
        
        # Padrão estático do Tibia 8.60 Clássico (Sem ASLR)
        self.base_address: int = 0x400000 

    def attach(self) -> bool:
        """Localiza o processo pelo nome, abre o handle e descobre o endereço base."""
        found_pid = None

        # 1. Localização segura via psutil
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                name = (proc.info["name"] or "").lower()
                if PROCESS_NAME.lower() in name:
                    found_pid = proc.info["pid"]
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if found_pid is None:
            self._log.error(f"Processo '{PROCESS_NAME}' não encontrado. O jogo está aberto?")
            return False

        self.process_id = found_pid

        # 2. Tentativa de obter o Handle com escalonamento de privilégios
        handle = kernel32.OpenProcess(PROCESS_RW_ACCESS, False, found_pid)

        if not handle:
            self.last_error = ctypes.get_last_error()
            self._log.debug(f"OpenProcess falhou com PROCESS_RW_ACCESS (WinError {self.last_error}). Tentando ALL_ACCESS...")
            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, found_pid)

            if not handle:
                self.last_error = ctypes.get_last_error()
                self._log.error(
                    f"Falha crítica ao anexar ao processo (WinError {self.last_error}). "
                    f"Execute o bot como Administrador ou verifique bloqueios de Anti-Cheat."
                )
                self.process_handle = None
                return False

        self.process_handle = handle
        self.last_error = None
        
        # 3. Integração ASLR: Resolve o endereço real do módulo principal na memória
        self.base_address = self._resolve_base_address()
        
        self._log.info(f"✓ Anexado com sucesso | PID: {self.process_id} | Base Address: {hex(self.base_address)}")
        return True

    def _resolve_base_address(self) -> int:
        """Utiliza a Win32 PSAPI para identificar o endereço onde o OS alocou o .exe."""
        if not self.process_handle:
            return 0x400000

        h_mods = (wintypes.HMODULE * 1024)()
        cb_needed = wintypes.DWORD()

        success = psapi.EnumProcessModulesEx(
            self.process_handle,
            h_mods,  # [CORREÇÃO]: Removido ctypes.byref()
            ctypes.sizeof(h_mods),
            ctypes.byref(cb_needed),
            LIST_MODULES_ALL
        )

        if success:
            # O índice [0] do EnumProcessModules é sistematicamente o executável principal (o próprio .exe)
            return h_mods[0]
        
        self._log.warning("Falha ao resolver Base Address dinâmico via PSAPI. Assumindo 0x400000.")
        return 0x400000

    def is_running(self) -> bool:
        """Verifica se o processo anexado ainda está ativo."""
        if self.process_handle is None or self.process_id is None:
            return False
        try:
            p = psutil.Process(self.process_id)
            return p.is_running()
        except psutil.NoSuchProcess:
            return False

    def ensure_attached(self) -> bool:
        """Garante que há um handle válido, tentando reanexar se necessário."""
        if self.process_handle and self.is_running():
            return True
        return self.attach()

    def detach(self) -> None:
        """Fecha o handle atual e libera recursos do SO."""
        if self.process_handle:
            kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.process_id = None
            self.base_address = 0x400000