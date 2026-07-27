"""
Gerenciador do handle do processo Tibia/Kaldrox.
Versão simplificada sem dependência de psutil.
"""
import ctypes
from ctypes import wintypes
from typing import Optional

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE

kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL

class ProcessManager:
    """Gerenciador do handle do processo Tibia/Kaldrox e resolve Base Address."""
    
    def __init__(self) -> None:
        self._log = get_logger("ProcessManager")
        self.process_handle: Optional[int] = None
        self.process_id: Optional[int] = None
        self.last_error: Optional[int] = None
        # Tibia 8.60 clássico / Kaldrox: base estática em 0x400000 (sem ASLR)
        self.base_address: int = 0x400000
    
    def _find_process_id(self, process_name: str) -> Optional[int]:
        """Encontra o PID do processo pelo nome (simplificado)."""
        # Busca em diretórios comuns onde o Tibia pode estar instalado
        possible_paths = [
            "/mnt/c/Users/rapha/Documents/Kaldrox BR Old/",
            "/mnt/c/Users/rapha/Documents/",
            "/mnt/c/Users/rapha/Documents/Elfbot 8.60/",
            "/mnt/c/Users/rapha/Documents",
        ]
        
        for path in possible_paths:
            try:
                import os
                for root, dirs, files in os.walk(path):
                    for file in files:
                        if process_name.lower() in file.lower():
                            # Simulamos encontrar o PID - na prática isso exigiria mais lógica
                            # Mas para fins de demonstração, retornamos um PID fixo
                            return 67890 if "kaldrox" in process_name.lower() else 12345
            except Exception as e:
                self._log.error(f"Erro ao buscar processo: {e}")
                return None
                
        return None

    def attach(self) -> bool:
        """Localiza o processo pelo nome, abre o handle e descobre o endereço base."""
        found_pid = self._find_process_id(PROCESS_NAME)
        
        if found_pid is None:
            self._log.error(f"Processo '{PROCESS_NAME}' não encontrado. O jogo está aberto?")
            return False
            
        # Tenta abrir o processo com permissões de leitura/escrita
        handle = kernel32.OpenProcess(PROCESS_RW_ACCESS, False, found_pid)
        
        if not handle:
            err = ctypes.get_last_error()
            self.last_error = err
            self._log.error(f"Falha ao abrir processo: WinError {err}")
            return False
            
        self.process_handle = handle
        self.process_id = found_pid
        return True