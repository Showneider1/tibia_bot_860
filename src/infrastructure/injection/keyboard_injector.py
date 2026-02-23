import time
import win32api
import win32con
import win32gui
from src.core.interfaces.injector_interface import ICommandInjector
from src.infrastructure.logging.logger import get_logger

class KeyboardInjector(ICommandInjector):
    """Injeção de comandos via mensagens do Windows (PostMessage) para rodar em background."""

    def __init__(self, window_title_hint: str = "Tibia") -> None:
        self._window_title_hint = window_title_hint
        self._hwnd = None
        self._log = get_logger("KeyboardInjector")

    def _find_window(self) -> bool:
        def callback(hwnd, result):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if self._window_title_hint.lower() in title.lower():
                    result.append(hwnd)
            return True

        result: list[int] = []
        win32gui.EnumWindows(callback, result)
        if result:
            self._hwnd = result[0]
            return True
        return False

    def focus_client(self) -> bool:
        """Ainda mantido por compatibilidade, mas idealmente não precisaremos usar."""
        if not self._hwnd and not self._find_window():
            return False
        try:
            win32gui.SetForegroundWindow(self._hwnd)
            time.sleep(0.05)
            return True
        except Exception:
            return False

    def send_key_background(self, vk_code: int) -> None:
        """Envia tecla para o cliente minimizado/em background."""
        if not self._hwnd and not self._find_window():
            self._log.warning("Janela do cliente não encontrada.")
            return

        # Envia a mensagem de KeyDown e KeyUp diretamente para a janela
        win32gui.PostMessage(self._hwnd, win32con.WM_KEYDOWN, vk_code, 0)
        time.sleep(0.02) # Delay humano e de processamento do client
        win32gui.PostMessage(self._hwnd, win32con.WM_KEYUP, vk_code, 0)

    def _send_text_background(self, text: str) -> None:
        """Digita texto em background (ótimo para magias)."""
        if not self._hwnd and not self._find_window():
            return
            
        for ch in text:
            vk = win32api.VkKeyScan(ch)
            self.send_key_background(vk)
            time.sleep(0.01)
            
        # Pressiona ENTER
        self.send_key_background(win32con.VK_RETURN)

    def cast_spell(self, spell_words: str) -> None:
        self._log.debug(f"Casting spell (background): {spell_words}")
        self._send_text_background(spell_words)

    def send_hotkey(self, key: str) -> None:
        """Envia F1-F12 em background."""
        mapping = {
            "F1": win32con.VK_F1, "F2": win32con.VK_F2, "F3": win32con.VK_F3,
            "F4": win32con.VK_F4, "F5": win32con.VK_F5, "F6": win32con.VK_F6,
            "F7": win32con.VK_F7, "F8": win32con.VK_F8, "F9": win32con.VK_F9,
            "F10": win32con.VK_F10, "F11": win32con.VK_F11, "F12": win32con.VK_F12,
        }
        vk = mapping.get(key.upper())
        if not vk:
            self._log.warning(f"Hotkey não suportada: {key}")
            return
        self.send_key_background(vk)