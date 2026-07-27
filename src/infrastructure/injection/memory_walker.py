"""
WindowWalker - Movimento via PostMessage(WM_KEYDOWN/WM_KEYUP) no HWND do Tibia 8.60.

Metodo identico ao ElfBot / XenoBot:
  PostMessage(hwnd, WM_KEYDOWN, vk_code, lParam)
  time.sleep(press_duration)
  PostMessage(hwnd, WM_KEYUP,   vk_code, lParam)

Por que PostMessage funciona (e WriteProcessMemory nao):
  - Tibia 8.60 processa movimento via WM_KEYDOWN na sua message queue.
  - PostMessage injeta diretamente na fila da janela alvo, SEM foco de
    desktop, SEM afetar outros processos.
  - WriteProcessMemory em go_to_x/y/z depende de thread interna do Tibia
    que nao esta ativa nesta build/servidor.

Assinatura de walk_to:
  walk_to(current: Position, destination: Position) -> bool

  A direcao e calculada como:
    dx = clamp(destination.x - current.x, -1, 1)
    dy = clamp(destination.y - current.y, -1, 1)

  CavebotScript deve passar a posicao atual do player e o proximo tile.

lParam encoding para WM_KEYDOWN/WM_KEYUP:
  Bits [0-15]:  repeat count = 1
  Bits [16-23]: scan code OEM
  Bit  [24]:    extended key flag
  Bit  [30]:    previous key state (1 no KEYUP)
  Bit  [31]:    transition state   (1 no KEYUP)

Mapeamento de direcao -> VK (numpad):
  NW(-1,-1)=VK_NUMPAD7  N(0,-1)=VK_NUMPAD8  NE(+1,-1)=VK_NUMPAD9
  W(-1, 0)=VK_NUMPAD4                        E(+1, 0)=VK_NUMPAD6
  SW(-1,+1)=VK_NUMPAD1  S(0,+1)=VK_NUMPAD2  SE(+1,+1)=VK_NUMPAD3
"""
import time
import ctypes
import ctypes.wintypes as wintypes
from typing import Optional, Tuple

import win32gui
import win32con

try:
    import win32process
except ImportError:
    win32process = None

from src.core.value_objects.position import Position
from src.infrastructure.logging.logger import get_logger

# ---------------------------------------------------------------------------
# WinAPI - PostMessage
# ---------------------------------------------------------------------------

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_user32.PostMessageW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]
_user32.PostMessageW.restype = wintypes.BOOL

# ---------------------------------------------------------------------------
# Tabela VK + scancode para as 8 direcoes (numpad)
# (dx, dy) -> (vk_code, scan_code, is_extended)
# ---------------------------------------------------------------------------

_DIR_TO_VK: dict[Tuple[int, int], Tuple[int, int, bool]] = {
    ( 0, -1): (win32con.VK_NUMPAD8, 0x48, False),   # Norte
    ( 0, +1): (win32con.VK_NUMPAD2, 0x50, False),   # Sul
    (-1,  0): (win32con.VK_NUMPAD4, 0x4B, False),   # Oeste
    (+1,  0): (win32con.VK_NUMPAD6, 0x4D, False),   # Leste
    (-1, -1): (win32con.VK_NUMPAD7, 0x47, False),   # NW
    (+1, -1): (win32con.VK_NUMPAD9, 0x49, False),   # NE
    (-1, +1): (win32con.VK_NUMPAD1, 0x4F, False),   # SW
    (+1, +1): (win32con.VK_NUMPAD3, 0x51, False),   # SE
}

# Duracao do press em segundos (ElfBot usa ~40ms)
_PRESS_DURATION = 0.040


def _make_lparam(scan: int, extended: bool, key_up: bool) -> int:
    """
    Monta o lParam para WM_KEYDOWN / WM_KEYUP.
    Bits [0-15]  = repeat count (1)
    Bits [16-23] = scan code OEM
    Bit  [24]    = extended key
    Bit  [30]    = previous key state (1 = KEYUP)
    Bit  [31]    = transition state   (1 = KEYUP)
    """
    lp = 1
    lp |= (scan & 0xFF) << 16
    if extended:
        lp |= (1 << 24)
    if key_up:
        lp |= (1 << 30)
        lp |= (1 << 31)
    return lp


# ---------------------------------------------------------------------------
# MemoryWalker (implementado como WindowWalker internamente)
# ---------------------------------------------------------------------------

class MemoryWalker:
    """
    Controla o movimento do personagem via PostMessage(WM_KEYDOWN/WM_KEYUP)
    diretamente na message queue da janela do Tibia 8.60.

    Assinatura de walk_to ATUALIZADA:
        walk_to(current: Position, destination: Position) -> bool

    BotEngine e CavebotScript devem passar AMBAS as posicoes.
    A direcao e calculada deterministicamente sem estado interno fragil.

    Para compatibilidade com codigo legado que chama walk_to(destination),
    o parametro 'current' tem default None - nesse caso a direcao e inferida
    pelo _last_destination (comportamento anterior, menos confiavel).
    """

    DEFAULT_STEP_DELAY = 0.45

    def __init__(self, memory_writer=None, window_title_hint: str = "Tibia") -> None:
        self._window_title_hint = window_title_hint
        self._log = get_logger("MemoryWalker")
        self._hwnd: Optional[int] = None
        self._last_step_time: float = 0.0

    # ------------------------------------------------------------------
    # HWND
    # ------------------------------------------------------------------

    def set_hwnd(self, hwnd: int) -> None:
        """Injeta HWND diretamente (chamado pelo BotEngine apos attach)."""
        self._hwnd = hwnd
        self._log.debug(f"HWND definido: {hwnd:#010x}")

    def _find_hwnd(self) -> bool:
        result: list[int] = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and self._window_title_hint.lower() in title.lower():
                    result.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            self._log.debug(f"EnumWindows falhou: {e}")
            return False

        if result:
            self._hwnd = result[0]
            self._log.debug(f"HWND encontrado via titulo: {self._hwnd:#010x}")
            return True

        self._log.warning("Janela Tibia nao encontrada.")
        return False

    def _ensure_hwnd(self) -> bool:
        if self._hwnd:
            return True
        return self._find_hwnd()

    # ------------------------------------------------------------------
    # Envio da tecla
    # ------------------------------------------------------------------

    def _post_key(self, vk: int, scan: int, extended: bool) -> bool:
        lp_down = _make_lparam(scan, extended, key_up=False)
        lp_up   = _make_lparam(scan, extended, key_up=True)

        ok_down = _user32.PostMessageW(self._hwnd, win32con.WM_KEYDOWN, vk, lp_down)
        time.sleep(_PRESS_DURATION)
        ok_up   = _user32.PostMessageW(self._hwnd, win32con.WM_KEYUP,   vk, lp_up)

        if not ok_down or not ok_up:
            err = ctypes.get_last_error()
            self._log.warning(
                f"PostMessage falhou: hwnd={self._hwnd:#010x} "
                f"vk=0x{vk:02X} WinError={err}"
            )
            return False
        return True

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def walk_to(self, current: Position, destination: Position) -> bool:
        """
        Envia um passo de movimento via PostMessage(WM_KEYDOWN/WM_KEYUP).

        Parametros:
            current:     posicao atual do player (player.position)
            destination: tile destino (proximo passo do path)

        A direcao e calculada deterministicamente:
            dx = clamp(destination.x - current.x, -1, 1)
            dy = clamp(destination.y - current.y, -1, 1)

        Retorna True se PostMessage enviado com sucesso.
        """
        if not self._ensure_hwnd():
            return False

        dx = max(-1, min(1, destination.x - current.x))
        dy = max(-1, min(1, destination.y - current.y))

        if dx == 0 and dy == 0:
            self._log.debug("walk_to: current == destination, sem movimento.")
            return False

        entry = _DIR_TO_VK.get((dx, dy))
        if not entry:
            self._log.warning(f"Direcao sem mapeamento: dx={dx} dy={dy}")
            return False

        vk, scan, extended = entry
        ok = self._post_key(vk, scan, extended)

        if ok:
            self._last_step_time = time.time()
            self._log.debug(
                f"walk_to ({current.x},{current.y}) -> "
                f"({destination.x},{destination.y}) "
                f"dir=({dx},{dy}) vk=0x{vk:02X} OK"
            )
        return ok

    def cooldown_passed(self, step_delay: float = DEFAULT_STEP_DELAY) -> bool:
        """True se ja passou step_delay segundos desde o ultimo passo."""
        return (time.time() - self._last_step_time) >= step_delay

    def reset(self) -> None:
        """Reseta estado interno (chamado ao desativar cavebot ou parar engine)."""
        self._last_step_time = 0.0
        self._log.debug("WindowWalker resetado.")
