import time
import win32api
import win32con
import win32gui
from src.core.interfaces.injector_interface import ICommandInjector
from src.infrastructure.logging.logger import get_logger

# Mapeamento: vk_code -> (scancode, extended_key)
# extended_key=True para setas e teclas do bloco de navegacao.
# Numpad NAO usa extended bit.
_VK_SCAN_MAP = {
    win32con.VK_UP:      (0x48, True),
    win32con.VK_DOWN:    (0x50, True),
    win32con.VK_LEFT:    (0x4B, True),
    win32con.VK_RIGHT:   (0x4D, True),
    win32con.VK_NUMPAD1: (0x4F, False),
    win32con.VK_NUMPAD2: (0x50, False),
    win32con.VK_NUMPAD3: (0x51, False),
    win32con.VK_NUMPAD4: (0x4B, False),
    win32con.VK_NUMPAD5: (0x4C, False),
    win32con.VK_NUMPAD6: (0x4D, False),
    win32con.VK_NUMPAD7: (0x47, False),
    win32con.VK_NUMPAD8: (0x48, False),
    win32con.VK_NUMPAD9: (0x49, False),
    win32con.VK_RETURN:  (0x1C, False),
}


def _make_lparam(vk_code: int, key_up: bool = False) -> int:
    """
    Monta o lParam correto para WM_KEYDOWN / WM_KEYUP.

    Formato do lParam (32 bits):
      bits  0-15  : repeat count (1)
      bits 16-23  : OEM scan code
      bit  24     : extended key flag (1 para setas, PgUp, etc.)
      bits 25-28  : reservados (0)
      bit  29     : context code (0 para WM_KEYDOWN)
      bit  30     : previous key state (1 no key_up)
      bit  31     : transition state (0=down, 1=up)
    """
    entry = _VK_SCAN_MAP.get(vk_code)
    if entry:
        scancode, extended = entry
    else:
        # Fallback: usa MapVirtualKey para obter o scancode
        scancode = win32api.MapVirtualKey(vk_code, 0) & 0xFF
        extended = False

    lParam = 1                          # repeat count
    lParam |= (scancode & 0xFF) << 16   # scan code
    if extended:
        lParam |= (1 << 24)             # extended key
    if key_up:
        lParam |= (1 << 30)             # previous state: down
        lParam |= (1 << 31)             # transition: key released
    return lParam


class KeyboardInjector(ICommandInjector):
    """Injecao de comandos via PostMessage para rodar em background."""

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
            self._log.debug(f"Janela Tibia encontrada: hwnd={self._hwnd}")
            return True
        self._log.warning("Janela Tibia NAO encontrada.")
        return False

    def focus_client(self) -> bool:
        """Mantido por compatibilidade."""
        if not self._hwnd and not self._find_window():
            return False
        try:
            win32gui.SetForegroundWindow(self._hwnd)
            time.sleep(0.05)
            return True
        except Exception:
            return False

    def send_key_background(self, vk_code: int) -> None:
        """
        Envia tecla ao cliente Tibia em background via PostMessage.

        BUG-H CORRIGIDO: lParam=0 era ignorado pelo Tibia 8.60.
        O cliente verifica o scancode (bits 16-23) e o extended key
        flag (bit 24) no lParam. _make_lparam() monta o valor correto
        para cada vk_code, incluindo setas (extended=True) e numpad.
        """
        if not self._hwnd and not self._find_window():
            self._log.warning("Janela do cliente nao encontrada.")
            return

        lp_down = _make_lparam(vk_code, key_up=False)
        lp_up   = _make_lparam(vk_code, key_up=True)

        win32gui.PostMessage(self._hwnd, win32con.WM_KEYDOWN, vk_code, lp_down)
        time.sleep(0.02)
        win32gui.PostMessage(self._hwnd, win32con.WM_KEYUP,   vk_code, lp_up)

    def _send_text_background(self, text: str) -> None:
        """Digita texto em background (para magias)."""
        if not self._hwnd and not self._find_window():
            return
        for ch in text:
            vk = win32api.VkKeyScan(ch) & 0xFF
            self.send_key_background(vk)
            time.sleep(0.01)
        self.send_key_background(win32con.VK_RETURN)

    def cast_spell(self, spell_words: str) -> None:
        self._log.debug(f"Casting spell (background): {spell_words}")
        self._send_text_background(spell_words)

    def send_hotkey(self, key: str) -> None:
        """Envia F1-F12 em background."""
        mapping = {
            "F1":  win32con.VK_F1,  "F2":  win32con.VK_F2,  "F3":  win32con.VK_F3,
            "F4":  win32con.VK_F4,  "F5":  win32con.VK_F5,  "F6":  win32con.VK_F6,
            "F7":  win32con.VK_F7,  "F8":  win32con.VK_F8,  "F9":  win32con.VK_F9,
            "F10": win32con.VK_F10, "F11": win32con.VK_F11, "F12": win32con.VK_F12,
        }
        vk = mapping.get(key.upper())
        if not vk:
            self._log.warning(f"Hotkey nao suportada: {key}")
            return
        self.send_key_background(vk)
