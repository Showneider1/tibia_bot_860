"""
MemoryWalker - Movimento via SendInput + KEYEVENTF_SCANCODE.

Diagnostico historico:
  v1 - PostMessage(WM_KEYDOWN/WM_KEYUP): digitava no chat quando o chat
       box tinha foco interno no Tibia (BUG-POSTMESSAGE).
  v2 - WriteProcessMemory nos enderecos go_to_x/y/z (TibiaAPI 0x63FED4):
       WPM retornava OK mas o personagem nao se movia. Os enderecos GoTo
       sao reconhecidos pelo cliente oficial, mas nao pelo servidor Kaldrox.
  v3 (atual) - SendInput via KeyboardInjector.send_key_background(vk).
       SendInput injeta no fluxo global do Windows (GetAsyncKeyState),
       que o Tibia 8.60 le para processar o movimento. Nao exige foco da
       janela. Nao digita no chat (KEYEVENTF_SCANCODE, sem wVk).

Arquitetura:
  walk_to(current, destination) calcula dx/dy, mapeia para VK Numpad e
  delega para self._injector.send_key_background(vk). O injector ja tem
  toda a infraestrutura SendInput testada e funcionando (keyboard_injector.py).

Mapa direcional Numpad:
  (dx=0, dy=-1) Norte -> VK_NUMPAD8
  (dx=0, dy=+1) Sul   -> VK_NUMPAD2
  (dx=-1,dy=0)  Oeste -> VK_NUMPAD4
  (dx=+1,dy=0)  Leste -> VK_NUMPAD6
  (dx=-1,dy=-1) NW    -> VK_NUMPAD7
  (dx=+1,dy=-1) NE    -> VK_NUMPAD9
  (dx=-1,dy=+1) SW    -> VK_NUMPAD1
  (dx=+1,dy=+1) SE    -> VK_NUMPAD3
"""
import time
from typing import Optional

import win32con

from src.core.value_objects.position import Position
from src.infrastructure.logging.logger import get_logger

# Mapa (dx, dy) -> VK code Numpad
_DIR_TO_VK = {
    ( 0, -1): win32con.VK_NUMPAD8,  # Norte
    ( 0,  1): win32con.VK_NUMPAD2,  # Sul
    (-1,  0): win32con.VK_NUMPAD4,  # Oeste
    ( 1,  0): win32con.VK_NUMPAD6,  # Leste
    (-1, -1): win32con.VK_NUMPAD7,  # Noroeste
    ( 1, -1): win32con.VK_NUMPAD9,  # Nordeste
    (-1,  1): win32con.VK_NUMPAD1,  # Sudoeste
    ( 1,  1): win32con.VK_NUMPAD3,  # Sudeste
}


class MemoryWalker:
    """
    Controla o movimento do personagem via SendInput (KEYEVENTF_SCANCODE).

    Delega para KeyboardInjector.send_key_background(vk) que ja usa a
    implementacao correta de SendInput para o Tibia 8.60.

    Parametros do construtor:
        memory_writer:      ignorado (mantido por compatibilidade de assinatura
                            com BotEngine que passa memory_writer).
        window_title_hint:  ignorado (SendInput nao usa HWND).
    """

    DEFAULT_STEP_DELAY = 0.45

    def __init__(self, memory_writer=None, window_title_hint: str = "Tibia") -> None:
        self._injector = None  # injetado via set_injector() pelo BotEngine
        self._log = get_logger("MemoryWalker")
        self._last_step_time: float = 0.0

        # memory_writer ignorado nesta versao - SendInput nao usa WPM
        if memory_writer is not None:
            self._log.debug(
                "memory_writer recebido mas ignorado: "
                "MemoryWalker v3 usa SendInput via KeyboardInjector."
            )

    # ------------------------------------------------------------------
    # Injecao do KeyboardInjector (chamado pelo BotEngine.start())
    # ------------------------------------------------------------------

    def set_injector(self, injector) -> None:
        """
        Injeta o KeyboardInjector apos a instanciacao.
        Deve ser chamado pelo BotEngine logo apos start(), passando
        self._injector (o mesmo KeyboardInjector ja configurado com PID).
        """
        self._injector = injector
        self._log.debug("KeyboardInjector injetado no MemoryWalker.")

    def set_writer(self, memory_writer) -> None:
        """Mantido por compatibilidade - ignorado nesta versao."""
        self._log.debug("set_writer() chamado - ignorado (v3 usa SendInput).")

    def set_hwnd(self, hwnd: int) -> None:
        """Mantido por compatibilidade - ignorado nesta versao."""
        self._log.debug(
            f"set_hwnd({hwnd:#010x}) chamado - ignorado (SendInput nao usa HWND)."
        )

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def walk_to(self, current: Position, destination: Position) -> bool:
        """
        Envia um passo de movimento via SendInput.

        Calcula a direcao (dx, dy) entre current e destination,
        mapeia para o VK Numpad correspondente e chama
        self._injector.send_key_background(vk).

        Retorna True se a tecla foi enviada com sucesso.
        """
        if self._injector is None:
            self._log.error(
                "walk_to chamado sem KeyboardInjector! "
                "Chame bot_engine.walker.set_injector(bot_engine.injector) "
                "apos BotEngine.start()."
            )
            return False

        dx = max(-1, min(1, destination.x - current.x))
        dy = max(-1, min(1, destination.y - current.y))

        if dx == 0 and dy == 0:
            self._log.debug("walk_to: current == destination, sem movimento.")
            return False

        vk = _DIR_TO_VK.get((dx, dy))
        if vk is None:
            self._log.warning(f"walk_to: direcao ({dx},{dy}) nao mapeada.")
            return False

        try:
            self._injector.send_key_background(vk)
            self._last_step_time = time.time()
            self._log.debug(
                f"walk_to ({current.x},{current.y},{current.z}) -> "
                f"({destination.x},{destination.y},{destination.z}) "
                f"dir=({dx},{dy}) vk=0x{vk:02X} SendInput OK"
            )
            return True
        except Exception as e:
            self._log.error(f"walk_to SendInput erro: {e}", exc_info=True)
            return False

    def cooldown_passed(self, step_delay: float = DEFAULT_STEP_DELAY) -> bool:
        """True se ja passou step_delay segundos desde o ultimo passo."""
        return (time.time() - self._last_step_time) >= step_delay

    def reset(self) -> None:
        """Reseta estado interno (chamado ao desativar cavebot ou parar engine)."""
        self._last_step_time = 0.0
        self._log.debug("MemoryWalker resetado.")
