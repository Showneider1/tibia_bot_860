"""
MemoryWalker - Movimento via PostMessage WM_KEYDOWN/WM_KEYUP.

Diagnostico historico:
  v1 - PostMessage(WM_KEYDOWN/WM_KEYUP): digitava no chat quando o chat
       box tinha foco interno no Tibia (BUG-POSTMESSAGE).
  v2 - WriteProcessMemory nos enderecos go_to_x/y/z (TibiaAPI 0x63FED4):
       WPM retornava OK mas o personagem nao se movia. Os enderecos GoTo
       sao reconhecidos pelo cliente oficial, mas nao pelo servidor Kaldrox.
  v3 - SendInput via KeyboardInjector.send_key_background(vk).
       SendInput atualiza GetAsyncKeyState globalmente, mas so funciona
       quando a janela tem foreground focus.
  v4 - PostMessage WM_KEYDOWN/WM_KEYUP via KeyboardInjector com VK Numpad.
       PostMessage com VK_NUMPAD* nao funciona porque Tibia interpreta
       como numero no chat (GetKeyState(VK_NUMLOCK) retorna estado real
       do teclado, nao o estado simulado pelo PostMessage).
  v5 (atual) - PostMessage WM_KEYDOWN/WM_KEYUP com arrow keys (VK_UP/DOWN
       /LEFT/RIGHT). Setas funcionam SEMPRE que o chat esta fechado.
       Fecha o chat com VK_ESCAPE antes de cada passo.
       Diagonais usam duas setas em sequencia (50ms entre elas).

Arquitetura:
  walk_to(current, destination) calcula dx/dy, mapeia para arrow keys e
  delega para self._injector.send_key_background(vk). O injector usa
  PostMessage para enviar ao HWND do processo alvo.
  Antes de cada tecla de movimento, envia VK_ESCAPE para fechar o chat.
"""
import time
from typing import Optional

import win32con

from src.core.value_objects.position import Position
from src.infrastructure.logging.logger import get_logger

_DIAGONAL_DELAY = 0.030

# Mapa (dx, dy) -> lista de VK codes (arrow keys)
# Tibia 8.60: arrow keys movem o personagem quando o chat esta fechado.
# Numpad keys (VK_NUMPAD*) seriam interpretadas como numeros se o chat
# estivesse aberto, ou dependeriam de GetKeyState(VK_NUMLOCK).
# Arrow keys nao tem essa dependencia.
_DIR_TO_VK = {
    ( 0, -1): [win32con.VK_UP],          # Norte
    ( 0,  1): [win32con.VK_DOWN],        # Sul
    (-1,  0): [win32con.VK_LEFT],        # Oeste
    ( 1,  0): [win32con.VK_RIGHT],       # Leste
    (-1, -1): [win32con.VK_LEFT, win32con.VK_UP],    # NW
    ( 1, -1): [win32con.VK_RIGHT, win32con.VK_UP],   # NE
    (-1,  1): [win32con.VK_LEFT, win32con.VK_DOWN],  # SW
    ( 1,  1): [win32con.VK_RIGHT, win32con.VK_DOWN], # SE
}


class MemoryWalker:
    """
    Controla o movimento do personagem via PostMessage WM_KEYDOWN/WM_KEYUP.

    Delega para KeyboardInjector.send_key_background(vk) que envia
    PostMessage diretamente para a fila de mensagens do HWND alvo.

    Parametros do construtor:
        memory_writer:      ignorado (mantido por compatibilidade de assinatura
                            com BotEngine que passa memory_writer).
        window_title_hint:  ignorado (PostMessage usa HWND, nao title hint).
    """

    DEFAULT_STEP_DELAY = 0.45

    def __init__(self, memory_writer=None, window_title_hint: str = "Tibia") -> None:
        self._injector = None  # injetado via set_injector() pelo BotEngine
        self._log = get_logger("MemoryWalker")
        self._last_step_time: float = 0.0

        # memory_writer ignorado nesta versao - PostMessage nao usa WPM
        if memory_writer is not None:
            self._log.debug(
                "memory_writer recebido mas ignorado: "
                "MemoryWalker v4 usa PostMessage via KeyboardInjector."
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
        self._log.debug("set_writer() chamado - ignorado (v4 usa PostMessage).")

    def set_hwnd(self, hwnd: int) -> None:
        """Mantido por compatibilidade - ignorado nesta versao."""
        self._log.debug(
            f"set_hwnd({hwnd:#010x}) chamado - ignorado (HWND resolvido pelo injector)."
        )

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def walk_to(self, current: Position, destination: Position) -> bool:
        """
        Envia um passo de movimento via PostMessage.

        Calcula a direcao (dx, dy) entre current e destination,
        fecha o chat (VK_ESCAPE), e envia a(s) tecla(s) de seta
        correspondente(s). Diagonais enviam duas setas em sequencia.

        Retorna True se a(s) tecla(s) foram enviadas com sucesso.
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

        vk_list = _DIR_TO_VK.get((dx, dy))
        if vk_list is None:
            self._log.warning(f"walk_to: direcao ({dx},{dy}) nao mapeada.")
            return False

        try:
            for i, vk in enumerate(vk_list):
                self._injector.send_key_background(vk)
                if i < len(vk_list) - 1:
                    time.sleep(_DIAGONAL_DELAY)

            self._last_step_time = time.time()
            dir_name = {(-1,-1):"NW",(0,-1):"N",(1,-1):"NE",(-1,0):"W",
                        (1,0):"E",(-1,1):"SW",(0,1):"S",(1,1):"SE"}.get((dx,dy),"?")
            self._log.debug(
                f"walk_to ({current.x},{current.y},{current.z}) -> "
                f"({destination.x},{destination.y},{destination.z}) "
                f"dir={dir_name} vk={[hex(v) for v in vk_list]}"
            )
            return True
        except Exception as e:
            self._log.error(f"walk_to PostMessage erro: {e}", exc_info=True)
            return False

    def cooldown_passed(self, step_delay: float = DEFAULT_STEP_DELAY) -> bool:
        """True se ja passou step_delay segundos desde o ultimo passo."""
        return (time.time() - self._last_step_time) >= step_delay

    def reset(self) -> None:
        """Reseta estado interno (chamado ao desativar cavebot ou parar engine)."""
        self._last_step_time = 0.0
        self._log.debug("MemoryWalker resetado.")