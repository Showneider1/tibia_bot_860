"""
MemoryWalker - Movimento via injecao direta na memoria do Tibia 8.60.

Metodo identico ao ElfBot / XenoBot / TibiaAPI:
  1. Escreve coordenadas destino em go_to_x, go_to_y, go_to_z
  2. Seta current_tile_to_go = 1
  3. Seta tiles_to_go        = 1

O cliente Tibia le esses enderecos no seu proprio loop de movimento e
executa o passo diretamente, sem precisar de teclado, foco ou desktop
interativo. Funciona 100% em background.

Enderecos (Tibia 8.60 - definidos em addresses_860.py -> PLAYER_EXTRA):
  go_to_x:            0x63FED4
  go_to_y:            0x63FED8
  go_to_z:            0x63FEDC
  current_tile_to_go: 0x63FEA0
  tiles_to_go:        0x63FEA4
"""
import time
from typing import Optional

from src.core.value_objects.position import Position
from src.core.constants.addresses_860 import PLAYER_EXTRA
from src.infrastructure.memory.memory_writer import MemoryWriter
from src.infrastructure.logging.logger import get_logger


class MemoryWalker:
    """
    Controla o movimento do personagem escrevendo diretamente na memoria
    do processo Tibia - sem teclado, sem SendInput, sem foco de janela.

    Uso:
        walker = MemoryWalker(memory_writer)
        walker.walk_to(next_position)   # envia um passo
    """

    # Tibia 8.60 walk speed: ~470ms por tile em velocidade padrao.
    # 0.45s e seguro para personagens nivel 100+ sem haste.
    DEFAULT_STEP_DELAY = 0.45

    def __init__(self, memory_writer: MemoryWriter) -> None:
        self._writer = memory_writer
        self._log = get_logger("MemoryWalker")
        self._last_step_time: float = 0.0
        self._last_destination: Optional[Position] = None

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def walk_to(self, destination: Position) -> bool:
        """
        Injeta um passo de movimento para `destination` via memoria.

        Escreve em sequencia:
          go_to_x, go_to_y, go_to_z  -> coordenadas do tile destino
          current_tile_to_go         -> 1  (inicia contagem)
          tiles_to_go                -> 1  (1 tile a andar)

        Retorna True se a escrita foi bem-sucedida, False caso contrario.
        """
        ok = (
            self._writer.write_int(PLAYER_EXTRA["go_to_x"], destination.x)
            and self._writer.write_int(PLAYER_EXTRA["go_to_y"], destination.y)
            and self._writer.write_int(PLAYER_EXTRA["go_to_z"], destination.z)
            and self._writer.write_int(PLAYER_EXTRA["current_tile_to_go"], 1)
            and self._writer.write_int(PLAYER_EXTRA["tiles_to_go"], 1)
        )

        if ok:
            self._last_step_time = time.time()
            self._last_destination = destination
            self._log.debug(
                f"walk_to({destination.x},{destination.y},{destination.z}) OK"
            )
        else:
            self._log.warning(
                f"walk_to({destination.x},{destination.y},{destination.z}) FALHOU"
            )

        return ok

    def cooldown_passed(self, step_delay: float = DEFAULT_STEP_DELAY) -> bool:
        """Retorna True se ja passou step_delay segundos desde o ultimo passo."""
        return (time.time() - self._last_step_time) >= step_delay

    def reset(self) -> None:
        """Reseta o estado interno (chamado ao desativar o cavebot ou parar o engine)."""
        self._last_step_time = 0.0
        self._last_destination = None
