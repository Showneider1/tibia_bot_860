"""
KeyboardInjector - Injeta comandos de teclado no cliente Tibia 8.60.

Historico de correcoes:
  fix-1: PostMessage -> SendMessage (sincrono) para movimento
  fix-2: SendMessage -> SendInput (background real, sem bloquear thread)
  fix-3: WinError 87 (ERROR_INVALID_PARAMETER) no SendInput
         Causa: dwExtraInfo declarado como POINTER(c_ulong) mas o campo
         real e ULONG_PTR (inteiro). Ponteiro temporario era destruido
         pelo GC antes do SendInput ler. Corrigido para c_ulonglong = 0.
         Tambem: _INPUT_UNION sem _anonymous_ causava desalinhamento
         em 64-bit. Adicionado _anonymous_ = ('union',).

Tibia 8.60 processa movimento via GetKeyState/GetAsyncKeyState que leem
o estado fisico global do teclado. SendInput injeta diretamente nesse
fluxo, sem exigir foco da janela e sem bloquear o thread.
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
# WinAPI - INPUT / KEYBDINPUT corretos para SendInput no Windows 64-bit
#
# Referencia: https://learn.microsoft.com/en-us/windows/win32/api/winuser/ns-winuser-keybdinput
#
# KEYBDINPUT {
#   WORD      wVk;          // 2 bytes
#   WORD      wScan;        // 2 bytes
#   DWORD     dwFlags;      // 4 bytes
#   DWORD     time;         // 4 bytes
#   ULONG_PTR dwExtraInfo;  // 8 bytes em 64-bit (NAO e ponteiro, e inteiro)
# }
# ---------------------------------------------------------------------------

INPUT_KEYBOARD        = 1
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk",         wintypes.WORD),
        ("wScan",       wintypes.WORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        # ULONG_PTR: inteiro nativo de 8 bytes em 64-bit.
        # NAO use POINTER(c_ulong) — o ponteiro temporario e destruido
        # pelo GC antes do SendInput ler, causando WinError 87.
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    # _anonymous_ expoe os campos de _INPUT_UNION diretamente em INPUT,
    # garantindo alinhamento correto em 64-bit (igual ao layout C do Windows).
    _anonymous_ = ("union",)
    _fields_ = [
        ("type",  wintypes.DWORD),
        ("union", _INPUT_UNION),
    ]


# Tamanho da struct calculado uma unica vez (exigido pelo 3o argumento do SendInput)
_INPUT_SIZE = ctypes.sizeof(INPUT)

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.SendInput.argtypes = [
    wintypes.UINT,          # nInputs
    ctypes.POINTER(INPUT),  # pInputs
    ctypes.c_int,           # cbSize
]
_user32.SendInput.restype = wintypes.UINT

# Mapa VK -> (scancode OEM, extended_key)
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

    Usa KEYEVENTF_SCANCODE: Tibia reconhece a tecla pelo scancode OEM
    (independente do layout do teclado / ABNT2).
    wVk deve ser 0 quando KEYEVENTF_SCANCODE esta ativo.
    dwExtraInfo deve ser 0 (inteiro, nao ponteiro).
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
    inp.type         = INPUT_KEYBOARD
    inp.ki.wVk       = 0          # 0 obrigatorio com KEYEVENTF_SCANCODE
    inp.ki.wScan     = scancode
    inp.ki.dwFlags   = flags
    inp.ki.time      = 0
    inp.ki.dwExtraInfo = 0        # ULONG_PTR = inteiro 0, NAO ponteiro
    return inp


class KeyboardInjector(ICommandInjector):
    """
    Injeta teclas via SendInput para o cliente Tibia 8.60.

    SendInput injeta no fluxo global de input do Windows:
      - Atualiza GetKeyState/GetAsyncKeyState (lidos pelo Tibia para movimento)
      - Nao exige foco da janela alvo
      - Nao bloqueia o thread chamador
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
    # Resolucao de janela (mantida para focus_client / cast_spell)
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
        """Mantido por compatibilidade; nao e necessario para SendInput."""
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

        Sequencia: KEYDOWN -> sleep(25ms) -> KEYUP.
        25ms e o tempo minimo para o Tibia registrar a transicao de estado
        antes do KEYUP. Nao bloqueia o loop (cooldown gerenciado no cavebot).
        """
        inp_down = _build_input(vk_code, key_up=False)
        inp_up   = _build_input(vk_code, key_up=True)

        sent = _user32.SendInput(1, ctypes.byref(inp_down), _INPUT_SIZE)
        if sent != 1:
            err = ctypes.get_last_error()
            self._log.warning(
                f"SendInput(KEYDOWN) falhou: WinError {err} vk=0x{vk_code:02X}"
            )
            return

        time.sleep(0.025)

        _user32.SendInput(1, ctypes.byref(inp_up), _INPUT_SIZE)

    def _send_text_background(self, text: str) -> None:
        """Digita texto caractere a caractere (magias/chat)."""
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
