"""
WindowWalker - Movimento via PostMessage(WM_KEYDOWN/WM_KEYUP) no HWND do Tibia 8.60.

Metodo identico ao ElfBot / XenoBot:
  PostMessage(hwnd, WM_KEYDOWN, vk_code, lParam)
  time.sleep(press_duration)
  PostMessage(hwnd, WM_KEYUP,   vk_code, lParam)

Por que isso funciona (e WriteProcessMemory nao):
  - Tibia 8.60 processa movimento via WM_KEYDOWN na sua message queue.
  - PostMessage injeta a mensagem diretamente na fila da janela alvo,
    SEM precisar de foco de desktop, SEM afetar outros processos.
  - WriteProcessMemory nos enderecos go_to_x/y/z depende de uma thread
    interna do Tibia que nem sempre esta ativa (pathfinding desabilitado
    pelo servidor ou enderecos incorretos para esta build especifica).

lParam encoding para WM_KEYDOWN/WM_KEYUP:
  Bits [0-15]:  repeat count = 1
  Bits [16-23]: scan code OEM
  Bit  [24]:    extended key flag (setas = 1, numpad = 0)
  Bit  [29]:    context code = 0
  Bit  [30]:    previous key state (0 = KEYDOWN, 1 = KEYUP)
  Bit  [31]:    transition state  (0 = KEYDOWN, 1 = KEYUP)

Mapeamento de direcao -> VK:
  NW(-1,-1)=VK_NUMPAD7  N(0,-1)=VK_NUMPAD8  NE(+1,-1)=VK_NUMPAD9
  W(-1, 0)=VK_NUMPAD4                        E(+1, 0)=VK_NUMPAD6
  SW(-1,+1)=VK_NUMPAD1  S(0,+1)=VK_NUMPAD2  SE(+1,+1)=VK_NUMPAD3

Compatibilidade: interface identica ao MemoryWalker anterior.
  walk_to(destination: Position) -> bool
  cooldown_passed(step_delay: float) -> bool
  reset() -> None
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
# Tabela VK + scancode para as 8 direcoes + numpad
# ---------------------------------------------------------------------------

# (dx, dy) -> (vk_code, scan_code, is_extended)
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

# Duracao do press em segundos - ElfBot usa ~40ms
_PRESS_DURATION = 0.040


def _make_lparam(scan: int, extended: bool, key_up: bool) -> int:
    """
    Monta o lParam para WM_KEYDOWN / WM_KEYUP.

    Estrutura (32 bits):
      [0-15]  repeat count = 1
      [16-23] scan code
      [24]    extended key flag
      [29]    context code = 0
      [30]    previous key state (1 no KEYUP)
      [31]    transition state   (1 no KEYUP)
    """
    lp = 1                          # repeat count
    lp |= (scan & 0xFF) << 16
    if extended:
        lp |= (1 << 24)
    if key_up:
        lp |= (1 << 30)             # previous state = pressed
        lp |= (1 << 31)             # transition = release
    return lp


# ---------------------------------------------------------------------------
# WindowWalker
# ---------------------------------------------------------------------------

class MemoryWalker:
    """
    Controla o movimento do personagem via PostMessage(WM_KEYDOWN/WM_KEYUP)
    diretamente na message queue da janela do Tibia 8.60.

    Interface identica ao MemoryWalker anterior para compatibilidade total
    com BotEngine, CavebotScript e qualquer outro modulo que use bot_engine.walker.

    Uso:
        walker = MemoryWalker(memory_writer)   # memory_writer ignorado (compat)
        walker.walk_to(next_position)
    """

    DEFAULT_STEP_DELAY = 0.45

    def __init__(self, memory_writer=None, window_title_hint: str = "Tibia") -> None:
        """
        memory_writer: aceito por compatibilidade com BotEngine, nao utilizado.
        window_title_hint: substring do titulo da janela Tibia.
        """
        self._window_title_hint = window_title_hint
        self._log = get_logger("MemoryWalker")
        self._hwnd: Optional[int] = None
        self._last_step_time: float = 0.0
        self._last_destination: Optional[Position] = None

    # ------------------------------------------------------------------
    # Resolucao de HWND
    # ------------------------------------------------------------------

    def set_hwnd(self, hwnd: int) -> None:
        """Permite injetar o HWND diretamente (chamado pelo BotEngine apos attach)."""
        self._hwnd = hwnd
        self._log.debug(f"HWND definido externamente: {hwnd}")

    def _find_hwnd(self) -> bool:
        """Busca a janela do Tibia por titulo. Armazena em self._hwnd."""
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
            self._log.debug(f"Janela Tibia encontrada: hwnd={self._hwnd:#010x}")
            return True

        self._log.warning("Janela do Tibia nao encontrada para WindowWalker.")
        return False

    def _ensure_hwnd(self) -> bool:
        if self._hwnd:
            return True
        return self._find_hwnd()

    # ------------------------------------------------------------------
    # Nucleo de envio
    # ------------------------------------------------------------------

    def _post_key(self, vk: int, scan: int, extended: bool) -> bool:
        """
        Envia WM_KEYDOWN + sleep + WM_KEYUP no HWND do Tibia.
        Retorna True se ambos PostMessage retornaram != 0.
        """
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
    # API publica (identica ao MemoryWalker original)
    # ------------------------------------------------------------------

    def walk_to(self, destination: Position) -> bool:
        """
        Move o personagem um passo em direcao a `destination` via PostMessage.

        Calcula a direcao (dx, dy) entre a posicao atual inferida pelo
        destino e envia a tecla numpad correspondente no HWND do Tibia.

        Retorna True se o PostMessage foi enviado com sucesso.
        """
        if not self._ensure_hwnd():
            return False

        # Recupera a direcao a partir do ultimo destino conhecido vs novo destino.
        # CavebotScript ja calcula next_step relativo a posicao atual, entao
        # usamos destination diretamente para inferir a direcao via _last_destination.
        dx = 0
        dy = 0

        if self._last_destination is not None:
            raw_dx = destination.x - self._last_destination.x
            raw_dy = destination.y - self._last_destination.y
        else:
            # Primeiro passo: nao temos referencia; CavebotScript passa o tile
            # vizinho do player como destination, entao calculamos a direcao
            # relativa ao tile anterior via _last_destination = destination - 1 passo.
            # Sem referencia, nao ha como calcular - retorna False para aguardar.
            self._last_destination = destination
            self._log.debug(
                f"walk_to: primeiro passo sem referencia, aguardando proximo tick."
            )
            return False

        dx = max(-1, min(1, raw_dx))
        dy = max(-1, min(1, raw_dy))

        if dx == 0 and dy == 0:
            # Destino igual ao anterior - nao ha movimento
            return False

        entry = _DIR_TO_VK.get((dx, dy))
        if not entry:
            self._log.warning(f"Direcao invalida: dx={dx} dy={dy}")
            return False

        vk, scan, extended = entry

        ok = self._post_key(vk, scan, extended)
        if ok:
            self._last_step_time = time.time()
            self._last_destination = destination
            self._log.debug(
                f"walk_to({destination.x},{destination.y},{destination.z}) "
                f"-> vk=0x{vk:02X} dir=({dx},{dy}) OK"
            )
        return ok

    def cooldown_passed(self, step_delay: float = DEFAULT_STEP_DELAY) -> bool:
        """Retorna True se ja passou step_delay segundos desde o ultimo passo."""
        return (time.time() - self._last_step_time) >= step_delay

    def reset(self) -> None:
        """Reseta o estado interno (chamado ao desativar o cavebot ou parar o engine)."""
        self._last_step_time = 0.0
        self._last_destination = None
        self._log.debug("WindowWalker resetado.")
