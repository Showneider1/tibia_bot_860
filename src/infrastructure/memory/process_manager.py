"""
Gerenciador do handle do processo Tibia/Kaldrox.
Versão corrigida: usa CreateToolhelp32Snapshot para encontrar PID no Windows.
"""
import ctypes
import ctypes.wintypes as wintypes
from typing import Optional

from src.infrastructure.logging.logger import get_logger

# ---------------------------------------------------------------------------
# Constantes do processo
# ---------------------------------------------------------------------------
PROCESS_NAME = "Not Open.exe"       # nome do executável do cliente Tibia/Kaldrox
PROCESS_RW_ACCESS = 0x1F0FFF        # PROCESS_ALL_ACCESS (leitura + escrita)

# ---------------------------------------------------------------------------
# WinAPI declarations
# ---------------------------------------------------------------------------
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype  = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype  = wintypes.BOOL

# --- Toolhelp32 para enumerar processos sem psutil ---
TH32CS_SNAPPROCESS = 0x00000002

class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize",              wintypes.DWORD),
        ("cntUsage",            wintypes.DWORD),
        ("th32ProcessID",       wintypes.DWORD),
        ("th32DefaultHeapID",   ctypes.POINTER(ctypes.c_ulong)),
        ("th32ModuleID",        wintypes.DWORD),
        ("cntThreads",          wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase",      ctypes.c_long),
        ("dwFlags",             wintypes.DWORD),
        ("szExeFile",           ctypes.c_char * 260),
    ]

kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype  = wintypes.HANDLE

kernel32.Process32First.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32First.restype  = wintypes.BOOL

kernel32.Process32Next.argtypes  = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32)]
kernel32.Process32Next.restype   = wintypes.BOOL

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value


class ProcessManager:
    """Gerenciador do handle do processo Tibia/Kaldrox e resolve Base Address."""

    def __init__(self) -> None:
        self._log = get_logger("ProcessManager")
        self.process_handle: Optional[int] = None
        self.process_id:     Optional[int] = None
        self.last_error:     Optional[int] = None
        # Tibia 8.60 clássico / Kaldrox: base estática (sem ASLR)
        self.base_address: int = 0x400000

    # ------------------------------------------------------------------
    # Busca de PID via CreateToolhelp32Snapshot (Windows nativo)
    # ------------------------------------------------------------------

    def _find_process_id(self, process_name: str) -> Optional[int]:
        """Retorna o PID do primeiro processo cujo nome bate com process_name."""
        snapshot = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == INVALID_HANDLE_VALUE:
            err = ctypes.get_last_error()
            self._log.error(f"CreateToolhelp32Snapshot falhou: WinError {err}")
            return None

        entry = PROCESSENTRY32()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)

        pid: Optional[int] = None
        try:
            ok = kernel32.Process32First(snapshot, ctypes.byref(entry))
            while ok:
                exe = entry.szExeFile.decode("utf-8", errors="ignore")
                if exe.lower() == process_name.lower():
                    pid = entry.th32ProcessID
                    break
                ok = kernel32.Process32Next(snapshot, ctypes.byref(entry))
        finally:
            kernel32.CloseHandle(snapshot)

        return pid

    # ------------------------------------------------------------------
    # Attach / detach
    # ------------------------------------------------------------------

    def attach(self) -> bool:
        """Localiza o processo pelo nome e abre o handle com acesso total."""
        found_pid = self._find_process_id(PROCESS_NAME)

        if found_pid is None:
            self._log.error(
                f"Processo '{PROCESS_NAME}' não encontrado. O jogo está aberto?"
            )
            return False

        handle = kernel32.OpenProcess(PROCESS_RW_ACCESS, False, found_pid)

        if not handle:
            err = ctypes.get_last_error()
            self.last_error = err
            self._log.error(f"Falha ao abrir processo (PID={found_pid}): WinError {err}")
            return False

        self.process_handle = handle
        self.process_id = found_pid
        self._log.info(
            f"Processo '{PROCESS_NAME}' encontrado: PID={found_pid}, "
            f"base=0x{self.base_address:08X}"
        )
        return True

    def detach(self) -> None:
        """Fecha o handle do processo."""
        if self.process_handle:
            kernel32.CloseHandle(self.process_handle)
            self.process_handle = None
            self.process_id = None
            self._log.info("Handle do processo fechado.")

    def is_running(self) -> bool:
        """Retorna True se já há um handle aberto."""
        return self.process_handle is not None
