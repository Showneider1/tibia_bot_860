"""
Leitor de dados das Criaturas (Battle List) na memória do cliente Tibia.
"""
from typing import List, Dict, Any
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats
from src.infrastructure.memory.memory_reader import MemoryReader
from src.core.value_objects.address import MemoryAddress
from src.infrastructure.logging.logger import get_logger

class CreatureReader:
    """Responsável por extrair as criaturas da Battle List."""

    def __init__(self, memory_reader: MemoryReader, battle_list_addresses: Dict[str, Any], creature_offsets: Dict[str, int]):
        self._memory = memory_reader
        self._addresses = battle_list_addresses
        self._offsets = creature_offsets
        self._log = get_logger("CreatureReader")

    def get_creatures(self) -> List[Creature]:
        creatures = []
        try:
            start_addr: MemoryAddress = self._addresses["start"]
            step: int = self._addresses["step"]
            max_creatures: int = self._addresses["max_creatures"]

            for slot_index in range(max_creatures):
                try:
                    # CORREÇÃO 1: Usar with_offset em vez de soma (+)
                    creature_base_addr = start_addr.with_offset(slot_index * step)
                    
                    # CORREÇÃO 2: Aplicar o with_offset para ler os atributos
                    creature_id = self._memory.read_int(creature_base_addr.with_offset(self._offsets["id"]))
                    
                    # Se o ID for 0, o slot está vazio
                    if creature_id <= 0:
                        continue

                    # Lê os restantes atributos usando a mesma lógica segura
                    hp_percent = self._memory.read_int(creature_base_addr.with_offset(self._offsets["hp_bar"]))
                    x = self._memory.read_int(creature_base_addr.with_offset(self._offsets["x"]))
                    y = self._memory.read_int(creature_base_addr.with_offset(self._offsets["y"]))
                    z = self._memory.read_int(creature_base_addr.with_offset(self._offsets["z"]))
                    is_visible = self._memory.read_int(creature_base_addr.with_offset(self._offsets["visible"]))

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
                    stats = Stats(health=hp_bar, max_health=100, mana=0, max_mana=0)
                    position = Position(x, y, z)
                    name_clean = name.strip() if name else "Unknown"

                    creature = Creature(
                        id=creature_id,
                        name=name_clean,
                        position=position,
                        stats=stats,
                        visible=True,
                        walking=False,
                    )
                    creatures.append(creature)

                except Exception as e:
                    # Descomente a linha abaixo se quiser debugar erros individuais de slots no futuro
                    # self._log.debug(f"Erro ao ler criatura no slot {slot_index}: {e}")
                    continue

        except Exception as e:
            self._log.error(f"Erro crítico ao ler battle list: {e}")
        
        return creatures