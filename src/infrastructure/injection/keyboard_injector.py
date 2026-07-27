"""
KeyboardInjector - Injeta comandos de teclado no cliente Tibia 8.60.

Historico de correcoes:
  fix-1: PostMessage -> SendMessage (sincrono) para movimento
  fix-2: SendMessage -> SendInput (global, background real, sem bloquear thread)

Tibia 8.60 processa movimento via GetKeyState/GetAsyncKeyState que leem
o estado fisico global do teclado. PostMessage e asssincrono e nao atualiza
esse estado. SendMessage era sincrono mas bloqueava o thread por ~420ms.

SendInput injeta diretamente no fluxo de input do Windows (mesma fila que
teclas fisicas), atualizando GetKeyState sem exigir foco da janela e sem
bloqueio de thread. E o unico metodo que funciona em background real.

Arquitetura:
  - send_key_background(vk_code): SendInput KEYDOWN + sleep(25ms) + SendInput KEYUP
  - cast_spell / send_hotkey: continuam usando send_key_background
  - focus_client(): mantido por compatibilidade, nao e mais necessario
"""
import time
import ctypes
import ctypes.wintypes as wintypes
import win32con
import win32api
import win32gui
try:
    import win32process
except ImportError:
    win32process = None

from src.core.interfaces.injector_interface import ICommandInjector
from src.infrastructure.logging.logger import get_logger

# ---------------------------------------------------------------------------
# WinAPI - INPUT structures para SendInput
# ---------------------------------------------------------------------------

INPUT_KEYBOARD     = 1
KEYEVENTF_KEYUP    = 0x0002
KEYEVENTF_SCANCODE = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         wintypes.WORD),
        ("wScan",       wintypes.WORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type",  wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendInput.argtypes = [
    wintypes.UINT,
    ctypes.POINTER(INPUT),
    ctypes.c_int,
]
_user32.SendInput.restype = wintypes.UINT

# Mapa VK -> (scancode, extended)
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


def _build_input(vk_code: int, key_up: bool = False) -> INPUT:
    """
    Constroi struct INPUT para SendInput.
    Usa KEYEVENTF_SCANCODE para garantir que o Tibia reconheca a tecla
    pelo scancode OEM e nao pelo vk abstrato.
    """
    entry = _VK_SCAN_MAP.get(vk_code)
    if entry:
        scancode, extended = entry
    else:
        scancode = win32api.MapVirtualKey(vk_code, 0) & 0xFF
        extended = False

    flags = KEYEVENTF_SCANCODE
    if extended:
        flags |= KEYEVENTF_EXTENDEDKEY
    if key_up:
        flags |= KEYEVENTF_KEYUP

    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk   = 0          # deve ser 0 quando usando SCANCODE
    inp.union.ki.wScan = scancode
    inp.union.ki.dwFlags = flags
    inp.union.ki.time  = 0
    inp.union.ki.dwExtraInfo = ctypes.pointer(ctypes.c_ulong(0))
    return inp


class KeyboardInjector(ICommandInjector):
    """
    Injeta teclas via SendInput para o cliente Tibia.

    SendInput injeta no fluxo global de input do Windows, atualizando
    GetKeyState/GetAsyncKeyState sem exigir foco da janela e sem bloquear
    o thread chamador. E o unico metodo que funciona em background real
    no Tibia 8.60.
    """

    def __init__(
        self,
        window_title_hint: str = "Tibia",
        process_id: int | None = None,
    ) -> None:
        self._window_title_hint = window_title_hint
        self._process_id = process_id
        self._hwnd = None
        self._log = get_logger("KeyboardInjector")

    # ------------------------------------------------------------------
    # Resolucao de janela (mantida para focus_client e cast_spell)
    # ------------------------------------------------------------------

    def _find_window_by_pid(self, pid: int) -> bool:
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
            self._log.debug(f"EnumWindows(pid) falhou: {e}")
            return False

        if result:
            self._hwnd = result[0]
            self._log.debug(f"Janela por PID={pid}: hwnd={self._hwnd}")
            return True
        return False

    def _find_window_by_title(self) -> bool:
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
            self._log.debug(f"EnumWindows(title) falhou: {e}")
            return False

        if result:
            self._hwnd = result[0]
            self._log.debug(f"Janela por titulo: hwnd={self._hwnd}")
            return True
        return False

    def _find_window(self) -> bool:
        if self._process_id is not None:
            if self._find_window_by_pid(self._process_id):
                return True
            self._log.debug("PID nao mapeou janela visivel; fallback para titulo.")
        if self._find_window_by_title():
            return True
        self._log.warning("Janela do cliente nao encontrada.")
        return False

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def set_process_id(self, process_id: int | None) -> None:
        """Atualiza PID e invalida hwnd em cache."""
        self._process_id = process_id
        self._hwnd = None

    def focus_client(self) -> bool:
        """Nao e mais necessario para SendInput, mantido por compatibilidade."""
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
        Envia tecla via SendInput (background real).

        SendInput injeta no fluxo global de input do Windows:
          - Atualiza GetKeyState / GetAsyncKeyState (lidos pelo Tibia para movimento)
          - Nao exige foco da janela
          - Nao bloqueia o thread chamador
          - Tibia 8.60 processa o movimento normalmente

        Sequencia: KEYDOWN -> sleep(25ms) -> KEYUP
        O sleep de 25ms e o minimo para o cliente registrar a tecla
        antes do release; nao bloqueia o loop (ver cavebot_script.py).
        """
        inp_down = _build_input(vk_code, key_up=False)
        inp_up   = _build_input(vk_code, key_up=True)

        sent = _user32.SendInput(1, ctypes.byref(inp_down), ctypes.sizeof(INPUT))
        if sent != 1:
            err = ctypes.get_last_error()
            self._log.warning(f"SendInput(KEYDOWN) falhou: WinError {err} vk=0x{vk_code:02X}")
            return

        time.sleep(0.025)   # 25ms: minimo para Tibia registrar a tecla

        _user32.SendInput(1, ctypes.byref(inp_up), ctypes.sizeof(INPUT))

    def _send_text_background(self, text: str) -> None:
        """Digita texto em background (para magias/chat)."""
        for ch in text:
            vk = win32api.VkKeyScan(ch) & 0xFF
            self.send_key_background(vk)
            time.sleep(0.01)
        self.send_key_background(win32con.VK_RETURN)

    def cast_spell(self, spell_words: str) -> None:
        self._log.debug(f"Casting spell: {spell_words}")
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
