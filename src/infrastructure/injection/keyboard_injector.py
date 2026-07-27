import time
import ctypes
import ctypes.wintypes as wintypes
import win32api
import win32con
import win32gui
try:
    import win32process
except ImportError:
    win32process = None
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

# user32 via ctypes para SendMessage sincrono
_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32.SendMessageW.restype = ctypes.c_long


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
        scancode = win32api.MapVirtualKey(vk_code, 0) & 0xFF
        extended = False

    lParam = 1
    lParam |= (scancode & 0xFF) << 16
    if extended:
        lParam |= (1 << 24)
    if key_up:
        lParam |= (1 << 30)
        lParam |= (1 << 31)
    return lParam


class KeyboardInjector(ICommandInjector):
    """Injecao de comandos via SendMessage/PostMessage para o cliente Tibia."""

    def __init__(
        self,
        window_title_hint: str = "Tibia",
        process_id: int | None = None,
    ) -> None:
        """
        Injetor de teclas.

        Resolucao da janela alvo (ordem):
          1. process_id (se fornecido) - mais robusto, independe do titulo
          2. window_title_hint (fallback) - mantem compat com Tibia classico
        """
        self._window_title_hint = window_title_hint
        self._process_id = process_id
        self._hwnd = None
        self._log = get_logger("KeyboardInjector")

    # ------------------------------------------------------------------
    # Resolucao de janela
    # ------------------------------------------------------------------

    def _find_window_by_pid(self, pid: int) -> bool:
        """Localiza a janela visivel cujo processo dono tem o PID informado."""
        if win32process is None:
            return False
        result: list[int] = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
                except Exception:
                    hwnd_pid = 0
                if hwnd_pid == pid:
                    result.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(callback, result)
        except Exception as e:
            self._log.debug(f"EnumWindows falhou: {e}")
            return False

        if result:
            self._hwnd = result[0]
            self._log.debug(f"Janela encontrada por PID={pid}: hwnd={self._hwnd}")
            return True
        return False

    def _find_window_by_title(self) -> bool:
        """Localiza a janela visivel cujo titulo contem o hint (case-insensitive)."""
        result: list[int] = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and self._window_title_hint.lower() in title.lower():
                    result.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(callback, result)
        except Exception as e:
            self._log.debug(f"EnumWindows (title) falhou: {e}")
            return False

        if result:
            self._hwnd = result[0]
            self._log.debug(f"Janela encontrada por titulo: hwnd={self._hwnd}")
            return True
        return False

    def _find_window(self) -> bool:
        """
        Tenta localizar a janela do cliente. Ordem:
          1. por process_id (mais robusto)   - usado pelo Kaldrox
          2. por titulo (fallback)           - Tibia classico
        Retorna True se encontrou.
        """
        if self._process_id is not None:
            if self._find_window_by_pid(self._process_id):
                return True
            self._log.debug(
                f"PID {self._process_id} nao mapeou a uma janela visivel; caindo para titulo."
            )
        if self._find_window_by_title():
            return True
        self._log.warning("Janela do cliente nao encontrada.")
        return False

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def set_process_id(self, process_id: int | None) -> None:
        """Atualiza o PID e invalida hwnd em cache."""
        self._process_id = process_id
        self._hwnd = None

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
        Envia tecla ao cliente Tibia.

        Tibia 8.60 processa movimento via GetKeyState/GetAsyncKeyState,
        que leem o estado fisico — PostMessage e assincrono e nao atualiza
        esse estado, sendo ignorado para movimento.

        Solucao: WM_KEYDOWN via SendMessage (sincrono — aguarda o cliente
        processar antes de retornar) + WM_KEYUP via PostMessage.
        Isso garante que o cliente registre o movimento sem exigir foco
        exclusivo da janela.
        """
        if not self._hwnd and not self._find_window():
            self._log.warning("Janela do cliente nao encontrada.")
            return

        lp_down = _make_lparam(vk_code, key_up=False)
        lp_up   = _make_lparam(vk_code, key_up=True)

        # WM_KEYDOWN: SendMessage (sincrono) — cliente processa antes de retornar
        _user32.SendMessageW(
            self._hwnd,
            win32con.WM_KEYDOWN,
            vk_code,
            lp_down,
        )
        time.sleep(0.02)
        # WM_KEYUP: PostMessage (assincrono) — suficiente para liberar a tecla
        win32gui.PostMessage(self._hwnd, win32con.WM_KEYUP, vk_code, lp_up)

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
