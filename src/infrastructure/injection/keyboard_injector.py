"""
KeyboardInjector - Injeta comandos de teclado no cliente Tibia 8.60.

Historico de correcoes:
  fix-1: PostMessage -> SendMessage (sincrono) para movimento
  fix-2: SendMessage -> SendInput (background real, sem bloquear thread)
  fix-3: dwExtraInfo era POINTER(c_ulong); corrigido para c_ulonglong.
  fix-4: assert sizeof(INPUT)==28 errado para 64-bit (correto: 32).
         Padding manual (_pad, _pad_ki) causava sizeof=32 em 32-bit e
         tamanhos errados em 64-bit. Removidos: ctypes calcula o padding
         correto automaticamente quando os tipos sao declarados sem
         campos de padding manuais.
         sizeof esperado: 28 em 32-bit, 32 em 64-bit.
         SendInput atomico (array[KEYDOWN, KEYUP]) mantido.
  v4:    SendInput -> PostMessage WM_KEYDOWN/WM_KEYUP.
         SendInput so funciona para foreground window. PostMessage envia
         diretamente para a fila de mensagens da janela alvo (HWND),
         funcionando em background. Movimento usa teclas Numpad que o
         Tibia processa mesmo com chat aberto.
         Metodo identico ao usado por ElfBot/XenoBot.

Tibia 8.60 processa movimento via window proc. PostMessage(WM_KEYDOWN/WM_KEYUP)
injeta na fila de mensagens da janela alvo sem exigir foco.
"""
import sys
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
# WinAPI structs para SendInput
#
# sizeof(INPUT) esperado pelo Windows:
#   32-bit: DWORD(4) + union(24) = 28  [ULONG_PTR=4, KEYBDINPUT=16]
#   64-bit: DWORD(4) + pad(4) + union(24) = 32  [ULONG_PTR=8, KEYBDINPUT=24]
#
# NAO inserir campos de padding manual: o ctypes calcula automaticamente
# o alinhamento correto para cada plataforma quando os tipos reais sao
# declarados. Padding manual quebra o calculo em uma das arquiteturas.
# ---------------------------------------------------------------------------

INPUT_KEYBOARD        = 1
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001


class KEYBDINPUT(ctypes.Structure):
    """Layout identico ao KEYBDINPUT do Windows SDK."""
    _fields_ = [
        ("wVk",         wintypes.WORD),
        ("wScan",       wintypes.WORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        # ULONG_PTR: 4 bytes em 32-bit, 8 bytes em 64-bit.
        # c_ulonglong garante 8 bytes em ambos; o ctypes insere o padding
        # de alinhamento necessario antes deste campo automaticamente.
        ("dwExtraInfo", ctypes.c_ulonglong),
    ]


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    # _anonymous_ expoe 'ki' diretamente em INPUT (inp.ki.wVk)
    _anonymous_ = ("u",)
    _fields_ = [
        ("type", wintypes.DWORD),
        ("u",    _INPUT_UNION),
    ]


# sizeof esperado:
#   32-bit Python: 28
#   64-bit Python: 32
_POINTER_SIZE   = ctypes.sizeof(ctypes.c_void_p)
_EXPECTED_SIZES = {4: 28, 8: 32}
_EXPECTED_SIZE  = _EXPECTED_SIZES.get(_POINTER_SIZE)
_INPUT_SIZE     = ctypes.sizeof(INPUT)

if _EXPECTED_SIZE is not None:
    assert _INPUT_SIZE == _EXPECTED_SIZE, (
        f"sizeof(INPUT)={_INPUT_SIZE} != {_EXPECTED_SIZE} "
        f"(ponteiro={_POINTER_SIZE} bytes). "
        "Layout da struct incorreto; SendInput vai retornar WinError 87."
    )

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

    KEYEVENTF_SCANCODE: Tibia identifica a tecla pelo scancode OEM,
    ignorando o layout do teclado (ABNT2 / US). wVk = 0 obrigatorio.
    dwExtraInfo = 0 (inteiro ULONG_PTR, nao ponteiro).
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
    inp.type           = INPUT_KEYBOARD
    inp.ki.wVk         = 0
    inp.ki.wScan       = scancode
    inp.ki.dwFlags     = flags
    inp.ki.time        = 0
    inp.ki.dwExtraInfo = 0
    return inp


class KeyboardInjector(ICommandInjector):
    """
    Injeta teclas via PostMessage WM_KEYDOWN/WM_KEYUP no HWND do cliente.

    PostMessage envia eventos diretamente para a fila de mensagens da janela
    alvo, sem exigir foreground. Movimento usa VK Numpad (Tibia processa
    mesmo com chat aberto). Cast de magias envia texto caractere a caractere
    (Tibia abre chat automaticamente).
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
    # Resolucao de janela
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
        """Mantido por compatibilidade; nao e necessario para PostMessage."""
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
        Envia KEYDOWN + KEYUP via PostMessage para o HWND alvo.

        PostMessage(WM_KEYDOWN/KEYUP, vk, lParam) injeta na fila de mensagens
        da janela do Tibia. Funciona em background (sem foreground).
        Movement keys (Numpad) sao processadas mesmo com chat aberto.

        lParam bits:
          0-15:  repeat count (1)
          16-23: scancode
          24:    extended key flag (setas)
          30:    previous key state (0=up, 1=down)
          31:    transition state (0=press, 1=release)

        sleep(35ms) pos-envio: garante processamento antes do proximo tick.
        """
        if not self._hwnd and not self._find_window():
            self._log.error("HWND nao encontrado para PostMessage")
            return

        scancode = win32api.MapVirtualKey(vk_code, 0) & 0xFF

        extended = 0x01000000 if vk_code in (
            win32con.VK_UP, win32con.VK_DOWN, win32con.VK_LEFT, win32con.VK_RIGHT,
            win32con.VK_PRIOR, win32con.VK_NEXT, win32con.VK_END, win32con.VK_HOME,
            win32con.VK_INSERT, win32con.VK_DELETE, win32con.VK_APPS,
        ) else 0

        lparam_down = 1 | (scancode << 16) | extended
        lparam_up   = 1 | (scancode << 16) | extended | (1 << 30) | (1 << 31)

        try:
            win32gui.PostMessage(self._hwnd, win32con.WM_KEYDOWN, vk_code, lparam_down)
            time.sleep(0.035)
            win32gui.PostMessage(self._hwnd, win32con.WM_KEYUP, vk_code, lparam_up)
            self._log.debug(f"PostMessage OK vk=0x{vk_code:02X}")
        except Exception as e:
            self._log.error(f"PostMessage falhou vk=0x{vk_code:02X}: {e}")

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