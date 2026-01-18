import time
import win32api
import win32con
import win32gui
from src.core.interfaces.injector_interface import ICommandInjector
from src.infrastructure.logging.logger import get_logger


class KeyboardInjector(ICommandInjector):
    """Injeção de comandos via teclado na janela do cliente."""

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
        if not self._hwnd and not self._find_window():
            self._log.warning("Janela do cliente não encontrada.")
            return False
        try:
            win32gui.SetForegroundWindow(self._hwnd)
            time.sleep(0.05)
            return True
        except Exception as e:
            self._log.error("Erro ao focar cliente: %s", e)
            return False

    def _send_text(self, text: str) -> None:
        if not self.focus_client():
            return
        for ch in text:
            vk = win32api.VkKeyScan(ch)
            win32api.keybd_event(vk, 0, 0, 0)
            time.sleep(0.01)
            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
        # Enter
        win32api.keybd_event(win32con.VK_RETURN, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(win32con.VK_RETURN, 0, win32con.KEYEVENTF_KEYUP, 0)

    def cast_spell(self, spell_words: str) -> None:
        self._log.debug("Casting spell: %s", spell_words)
        self._send_text(spell_words)

    def send_hotkey(self, key: str) -> None:
        """Envia F1–F12, etc."""
        if not self.focus_client():
            return
        mapping = {
            "F1": win32con.VK_F1, "F2": win32con.VK_F2, "F3": win32con.VK_F3,
            "F4": win32con.VK_F4, "F5": win32con.VK_F5, "F6": win32con.VK_F6,
            "F7": win32con.VK_F7, "F8": win32con.VK_F8, "F9": win32con.VK_F9,
            "F10": win32con.VK_F10, "F11": win32con.VK_F11, "F12": win32con.VK_F12,
        }
        vk = mapping.get(key.upper())
        if not vk:
            self._log.warning("Hotkey não suportada: %s", key)
            return
        win32api.keybd_event(vk, 0, 0, 0)
        time.sleep(0.01)
        win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
