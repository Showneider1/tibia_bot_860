"""
Sistema de hotkeys globais.
"""
import keyboard
from typing import Callable, Dict
from src.infrastructure.logging.logger import get_logger


class HotkeyManager:
    """Gerenciador de hotkeys globais."""
    
    def __init__(self):
        self._hotkeys: Dict[str, Callable] = {}
        self._log = get_logger("HotkeyManager")
        self._enabled = False
    
    def register(self, hotkey: str, callback: Callable) -> None:
        """
        Registra hotkey.
        
        Args:
            hotkey: Combinação (ex: "ctrl+shift+a")
            callback: Função a executar
        """
        try:
            keyboard.add_hotkey(hotkey, callback)
            self._hotkeys[hotkey] = callback
            self._log.info(f"Hotkey registrada: {hotkey}")
        except Exception as e:
            self._log.error(f"Erro ao registrar hotkey '{hotkey}': {e}")
    
    def unregister(self, hotkey: str) -> None:
        """Remove hotkey."""
        if hotkey in self._hotkeys:
            try:
                keyboard.remove_hotkey(hotkey)
                del self._hotkeys[hotkey]
                self._log.info(f"Hotkey removida: {hotkey}")
            except Exception as e:
                self._log.error(f"Erro ao remover hotkey '{hotkey}': {e}")
    
    def unregister_all(self) -> None:
        """Remove todas as hotkeys."""
        for hotkey in list(self._hotkeys.keys()):
            self.unregister(hotkey)
    
    def enable(self) -> None:
        """Habilita hotkeys."""
        self._enabled = True
        self._log.info("Hotkeys habilitadas")
    
    def disable(self) -> None:
        """Desabilita hotkeys."""
        self._enabled = False
        self._log.info("Hotkeys desabilitadas")
