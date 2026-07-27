"""
MemoryWalker - Movimento via WriteProcessMemory nos enderecos go_to_x/y/z.

Metodo identico ao ElfBot / XenoBot:
  Escreve go_to_x, go_to_y, go_to_z e tiles_to_go diretamente na
  memoria do processo Tibia 8.60. O cliente processa o movimento
  internamente sem necessidade de foco de janela ou input de teclado.

Enderecos usados (TibiaAPI 8.60 / addresses_860.py PLAYER_EXTRA):
  go_to_x    = 0x63FED4  (Experience + 72)
  go_to_y    = 0x63FED8  (Experience + 76)
  go_to_z    = 0x63FEDC  (Experience + 80)
  tiles_to_go = 0x63FEA4

Por que WriteProcessMemory funciona (e PostMessage nao):
  - PostMessage(WM_KEYDOWN) injeta na message queue da janela principal.
    Quando o foco interno esta no chat box, os WM_KEYDOWN viram texto
    ('8888...') em vez de mover o personagem.
  - WriteProcessMemory escreve diretamente nos registros de movimento
    do cliente Tibia 8.60, que sao processados pelo loop interno
    independente de foco ou estado do chat.

Assinatura de walk_to:
  walk_to(current: Position, destination: Position) -> bool

  A direcao e calculada como:
    dx = clamp(destination.x - current.x, -1, 1)
    dy = clamp(destination.y - current.y, -1, 1)
    next_tile = Position(current.x + dx, current.y + dy, current.z)

  Escreve next_tile em go_to_x/y/z e tiles_to_go=1.
"""
import time
from typing import Optional

from src.core.value_objects.position import Position
from src.core.value_objects.address import MemoryAddress
from src.infrastructure.logging.logger import get_logger

# Enderecos PLAYER_EXTRA (TibiaAPI 8.60)
_ADDR_GO_TO_X    = MemoryAddress(0x63FED4)  # Experience + 72
_ADDR_GO_TO_Y    = MemoryAddress(0x63FED8)  # Experience + 76
_ADDR_GO_TO_Z    = MemoryAddress(0x63FEDC)  # Experience + 80
_ADDR_TILES_TO_GO = MemoryAddress(0x63FEA4)


class MemoryWalker:
    """
    Controla o movimento do personagem via WriteProcessMemory.

    Escreve diretamente nos registros go_to_x/y/z + tiles_to_go
    do cliente Tibia 8.60. Nao usa teclado, PostMessage ou HWND.

    Requer um memory_writer (MemoryWriter) com process_handle ativo.
    """

    DEFAULT_STEP_DELAY = 0.45

    def __init__(self, memory_writer=None, window_title_hint: str = "Tibia") -> None:
        """
        Parametros:
            memory_writer:      MemoryWriter instanciado pelo BotEngine.
                                Obrigatorio para funcionar; sem ele walk_to
                                retorna False com log de erro.
            window_title_hint:  Ignorado (mantido por compatibilidade de assinatura).
        """
        self._writer = memory_writer
        self._log = get_logger("MemoryWalker")
        self._last_step_time: float = 0.0

        if memory_writer is None:
            self._log.warning(
                "MemoryWalker instanciado sem memory_writer! "
                "walk_to retornara False ate um writer ser injetado via set_writer()."
            )

    # ------------------------------------------------------------------
    # Injecao tardia do writer (caso instanciado antes do attach)
    # ------------------------------------------------------------------

    def set_writer(self, memory_writer) -> None:
        """Injeta ou substitui o MemoryWriter apos a instanciacao."""
        self._writer = memory_writer
        self._log.debug("MemoryWriter injetado no MemoryWalker.")

    # set_hwnd mantido por compatibilidade - ignorado nesta implementacao
    def set_hwnd(self, hwnd: int) -> None:
        self._log.debug(
            f"set_hwnd({hwnd:#010x}) chamado - ignorado (WriteProcessMemory nao usa HWND)."
        )

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def walk_to(self, current: Position, destination: Position) -> bool:
        """
        Envia um passo de movimento via WriteProcessMemory.

        Parametros:
            current:     posicao atual do player (player.position)
            destination: tile destino (proximo passo do path)

        Calcula o proximo tile (1 sqm na direcao do destino) e escreve:
            go_to_x    = next_tile.x
            go_to_y    = next_tile.y
            go_to_z    = next_tile.z
            tiles_to_go = 1

        Retorna True se todos os writes foram bem-sucedidos.
        """
        if self._writer is None:
            self._log.error(
                "walk_to chamado sem MemoryWriter! "
                "Verifique se BotEngine.start() foi chamado antes de habilitar scripts."
            )
            return False

        dx = max(-1, min(1, destination.x - current.x))
        dy = max(-1, min(1, destination.y - current.y))

        if dx == 0 and dy == 0:
            self._log.debug("walk_to: current == destination, sem movimento.")
            return False

        next_x = current.x + dx
        next_y = current.y + dy
        next_z = current.z

        ok_x = self._writer.write_int(_ADDR_GO_TO_X,    next_x)
        ok_y = self._writer.write_int(_ADDR_GO_TO_Y,    next_y)
        ok_z = self._writer.write_int(_ADDR_GO_TO_Z,    next_z)
        ok_t = self._writer.write_int(_ADDR_TILES_TO_GO, 1)

        ok = ok_x and ok_y and ok_z and ok_t

        if ok:
            self._last_step_time = time.time()
            self._log.debug(
                f"walk_to ({current.x},{current.y},{current.z}) -> "
                f"({next_x},{next_y},{next_z}) "
                f"dir=({dx},{dy}) WPM OK"
            )
        else:
            self._log.warning(
                f"walk_to FALHOU: ok_x={ok_x} ok_y={ok_y} "
                f"ok_z={ok_z} ok_tiles={ok_t} "
                f"| handle={getattr(self._writer._pm, 'process_handle', 'N/A')}"
            )

        return ok

    def cooldown_passed(self, step_delay: float = DEFAULT_STEP_DELAY) -> bool:
        """True se ja passou step_delay segundos desde o ultimo passo."""
        return (time.time() - self._last_step_time) >= step_delay

    def reset(self) -> None:
        """Reseta estado interno (chamado ao desativar cavebot ou parar engine)."""
        self._last_step_time = 0.0
        self._log.debug("MemoryWalker resetado.")
