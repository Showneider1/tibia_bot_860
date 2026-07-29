"""
Leitor de dados das Criaturas (Battle List) na memoria do cliente Tibia.
"""
from typing import List, Dict, Any
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats
from src.infrastructure.memory.memory_reader import MemoryReader
from src.core.value_objects.address import MemoryAddress
from src.infrastructure.logging.logger import get_logger


class CreatureReader:
    """Responsavel por extrair as criaturas da Battle List."""

    def __init__(
        self,
        memory_reader: MemoryReader,
        battle_list_addresses: Dict[str, Any],
        creature_offsets: Dict[str, int],
    ):
        self._memory = memory_reader
        self._addresses = battle_list_addresses
        self._offsets = creature_offsets
        self._log = get_logger("CreatureReader")

    def get_creatures(self) -> List[Creature]:
        """Le todos os slots da BattleList e retorna criaturas validas."""
        creatures = []
        try:
            start_addr: MemoryAddress = self._addresses["start"]
            step: int                 = self._addresses["step"]
            max_creatures: int        = self._addresses["max_creatures"]

            for slot_index in range(max_creatures):
                try:
                    base = start_addr.with_offset(slot_index * step)

                    creature_id = self._memory.read_int(
                        base.with_offset(self._offsets["id"])
                    )
                    if creature_id <= 0:
                        continue  # slot vazio

                    x = self._memory.read_int(base.with_offset(self._offsets["x"]))
                    y = self._memory.read_int(base.with_offset(self._offsets["y"]))
                    z = self._memory.read_int(base.with_offset(self._offsets["z"]))

                    if x <= 0 or y <= 0:
                        continue  # posicao invalida

                    name_raw = self._memory.read_string(
                        base.with_offset(self._offsets["name"]),
                        max_length=40,
                    )
                    name = (name_raw.strip() if name_raw else "") or "Unknown"

                    hp_bar = self._memory.read_int(
                        base.with_offset(self._offsets["hp_bar"])
                    )

                    creatures.append(
                        Creature(
                            id=creature_id,
                            name=name,
                            position=Position(x, y, z),
                            stats=Stats(
                                health=max(0, min(hp_bar, 100)),
                                max_health=100,
                                mana=0,
                                max_mana=0,
                            ),
                            visible=True,
                            walking=False,
                            battle_slot=slot_index,
                        )
                    )

                except Exception:
                    continue

        except Exception as e:
            self._log.error(f"Erro critico ao ler battle list: {e}")

        return creatures
