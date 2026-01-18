"""
Creature Reader - Lê battle list (criaturas) da memória.
Fonte: TibiaAPI 8.60 (https://github.com/ianobermiller/tibiaapi)
"""
from typing import List
from src.core.entities.creature import Creature
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.logging.logger import get_logger


class CreatureReader:
    """Lê criaturas da battle list com tratamento robusto de erros."""

    def __init__(self, memory: MemoryReader, addresses: dict, creature_offsets: dict):
        """
        Args:
            memory: MemoryReader instance
            addresses: Dicionário com 'start', 'step', 'max_creatures' (ex: BATTLE_LIST)
            creature_offsets: Offsets de campos dentro de cada criatura (ex: CREATURE)
        """
        self._memory = memory
        self._addresses = addresses
        self._offsets = creature_offsets
        self._log = get_logger("CreatureReader")

    def get_creatures(self) -> List[Creature]:
        """
        Lê e retorna lista de criaturas visíveis.
        
        Returns:
            Lista de Creature objects encontrados na battle list.
        """
        creatures = []

        try:
            start_addr = self._addresses["start"]
            step = self._addresses["step"]
            max_creatures = self._addresses["max_creatures"]

            # Itera sobre slots da battle list
            for slot_index in range(max_creatures):
                creature_base_addr = start_addr + (slot_index * step)

                try:
                    # Tenta ler ID como validação rápida
                    creature_id = self._memory.read_int(creature_base_addr + self._offsets["id"])

                    # ID 0 = slot vazio
                    if creature_id == 0:
                        continue

                    # Validação: ID deve ser > 0
                    if creature_id < 0:
                        continue

                    # Lê dados da criatura
                    name = self._memory.read_string(
                        creature_base_addr + self._offsets["name"],
                        max_length=40
                    )
                    
                    x = self._memory.read_int(creature_base_addr + self._offsets["x"])
                    y = self._memory.read_int(creature_base_addr + self._offsets["y"])
                    z = self._memory.read_int(creature_base_addr + self._offsets["z"])
                    
                    hp_bar = self._memory.read_int(creature_base_addr + self._offsets["hp_bar"])
                    
                    # Validação: posição deve fazer sentido
                    if x < 0 or y < 0 or z < 0:
                        continue

                    # Cria objeto creature
                    creature = Creature(
                        id=creature_id,
                        name=name.strip() if name else "Unknown",
                        x=x,
                        y=y,
                        z=z,
                        hp_bar=hp_bar,
                    )

                    creatures.append(creature)

                except Exception as e:
                    # Loga erro de criatura específica mas continua
                    self._log.debug(f"Erro ao ler criatura no slot {slot_index}: {e}")
                    continue

            return creatures

        except Exception as e:
            self._log.error(f"Erro crítico ao ler battle list: {e}", exc_info=True)
            return []
