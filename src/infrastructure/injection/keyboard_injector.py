"""
KeyboardInjector - Injeta comandos de teclado no cliente Tibia 8.60.

Historico de correcoes:
  fix-1: PostMessage -> SendMessage (sincrono) para movimento
  fix-2: SendMessage -> SendInput (background real, sem bloquear thread)
  fix-3: WinError 87 - dwExtraInfo era POINTER(c_ulong), corrigido para
         c_ulonglong. _anonymous_ em INPUT adicionado.
  fix-4: WinError 87 persistia pois _anonymous_ ocultava a necessidade
         do padding de 4 bytes entre 'type' e a union em 64-bit.
         sizeof(INPUT) calculado pelo ctypes era 24; Windows exige 28.
         Corrigido com campo '_pad' explicito (c_uint32) em INPUT.
         SendInput agora envia KEYDOWN+KEYUP atomicamente (array de 2)
         sem sleep() interno; sleep(35ms) pos-envio garante processamento.

Tibia 8.60 processa movimento via GetAsyncKeyState que le o estado
global do teclado. SendInput injeta nesse fluxo sem exigir foco.
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
# WinAPI structs para SendInput - layout exato do Windows SDK (64-bit)
#
# Layout C esperado pelo Windows:
#
#   typedef struct tagINPUT {
#     DWORD     type;        // offset  0, size 4
#     // padding implicito   // offset  4, size 4  <-- ctypes NAO insere isso
#     union {                //             automaticamente sem _pad explicito
#       KEYBDINPUT ki;       // offset  8, size 20
#     };                     // total union: 20 bytes
#   } INPUT;                 // sizeof == 28 bytes (alinhado a 8 bytes)
#
# KEYBDINPUT layout:
#   WORD      wVk;           // offset  0, size 2
#   WORD      wScan;         // offset  2, size 2
#   DWORD     dwFlags;       // offset  4, size 4
#   DWORD     time;          // offset  8, size 4
#   // padding              // offset 12, size 4
#   ULONG_PTR dwExtraInfo;   // offset 16, size 8
#   // total: 24 bytes -> union size = 20 bytes (com padding final de 4?)
#   // Na pratica sizeof(KEYBDINPUT) == 20 no SDK do Windows
#
# Estrategia: declarar INPUT com '_pad' explicito de 4 bytes apos 'type'.
# Isso garante ki.wVk no offset correto e sizeof(INPUT) == 28.
# ---------------------------------------------------------------------------

INPUT_KEYBOARD        = 1
KEYEVENTF_KEYUP       = 0x0002
KEYEVENTF_SCANCODE    = 0x0008
KEYEVENTF_EXTENDEDKEY = 0x0001


class KEYBDINPUT(ctypes.Structure):
    """sizeof deve ser 20 bytes (igual ao Windows SDK KEYBDINPUT em 64-bit)."""
    _fields_ = [
        ("wVk",         wintypes.WORD),       # 2 bytes, offset 0
        ("wScan",       wintypes.WORD),       # 2 bytes, offset 2
        ("dwFlags",     wintypes.DWORD),      # 4 bytes, offset 4
        ("time",        wintypes.DWORD),      # 4 bytes, offset 8
        ("_pad_ki",     wintypes.DWORD),      # 4 bytes, offset 12 (alinha dwExtraInfo a 8)
        ("dwExtraInfo", ctypes.c_ulonglong),  # 8 bytes, offset 16
    ]  # total: 24 bytes -- union padding alinhar ao maior membro (8): ok


class _INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
    ]


class INPUT(ctypes.Structure):
    """
    sizeof(INPUT) deve ser 28 bytes em 64-bit.

    '_pad' de 4 bytes apos 'type' e obrigatorio:
    sem ele ctypes calcula sizeof==24 e SendInput retorna WinError 87.
    NAO usar _anonymous_: ele oculta a necessidade do padding.
    """
    _fields_ = [
        ("type",  wintypes.DWORD),   # 4 bytes, offset 0
        ("_pad",  wintypes.DWORD),   # 4 bytes, offset 4  <-- CRITICO
        ("union", _INPUT_UNION),     # 24 bytes, offset 8
    ]


# Valida o tamanho em tempo de importacao para detectar regressao rapido.
assert ctypes.sizeof(INPUT) == 28, (
    f"sizeof(INPUT)={ctypes.sizeof(INPUT)} != 28. "
    "Padding da struct esta errado; SendInput vai retornar WinError 87."
)

_INPUT_SIZE = ctypes.sizeof(INPUT)  # == 28

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
    inp.type              = INPUT_KEYBOARD
    inp._pad              = 0
    inp.union.ki.wVk      = 0        # 0 obrigatorio com KEYEVENTF_SCANCODE
    inp.union.ki.wScan    = scancode
    inp.union.ki.dwFlags  = flags
    inp.union.ki.time     = 0
    inp.union.ki._pad_ki  = 0
    inp.union.ki.dwExtraInfo = 0
    return inp


class KeyboardInjector(ICommandInjector):
    """
    Injeta teclas via SendInput para o cliente Tibia 8.60.

    SendInput atualiza GetKeyState/GetAsyncKeyState globalmente.
    Nao exige foco da janela. Nao bloqueia o thread chamador.
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
        Envia KEYDOWN + KEYUP via SendInput atomico (array de 2 eventos).

        Por que atomico:
          SendInput(2, [down, up], cbSize) injeta os dois eventos como um
          bloco indivisivel no fluxo de input do Windows. Isso garante que
          GetAsyncKeyState registre a transicao corretamente mesmo sob carga.
          O sleep(25ms) anterior entre down e up causava WinError 87 no KEYUP
          porque o GC podia coletar inp_down antes do Windows ler.

        sleep(35ms) pos-envio: da tempo ao Tibia de processar
        GetAsyncKeyState antes do proximo tick do cavebot.
        """
        inp_down = _build_input(vk_code, key_up=False)
        inp_up   = _build_input(vk_code, key_up=True)

        # Array de 2 INPUTs para envio atomico
        arr = (INPUT * 2)(inp_down, inp_up)

        sent = _user32.SendInput(2, arr, _INPUT_SIZE)
        if sent != 2:
            err = ctypes.get_last_error()
            self._log.warning(
                f"SendInput falhou: enviou {sent}/2, WinError {err} vk=0x{vk_code:02X}"
            )
            return

        self._log.debug(f"SendInput OK vk=0x{vk_code:02X}")
        # Aguarda o Tibia processar a transicao de estado do teclado
        time.sleep(0.035)

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
