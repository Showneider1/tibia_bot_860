"""
Leitor de dados do Player na memória do cliente Tibia.
"""
from typing import Dict, Optional

from src.core.entities.player import Player
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats
from src.infrastructure.memory.memory_reader import MemoryReader
from src.core.value_objects.address import MemoryAddress
from src.core.exceptions.memory_exceptions import MemoryReadError
from src.infrastructure.logging.logger import get_logger

class PlayerReader:
    """Responsável por extrair as informações do jogador da memória."""

    def __init__(self, memory_reader: MemoryReader, addresses: Dict[str, MemoryAddress]):
        self._memory = memory_reader
        self._addresses = addresses
        self._log = get_logger("PlayerReader")

def get_player(self) -> Optional[Player]:
         """Lê os endereços de memória e constrói a entidade Player."""
         try:
             self._log.debug("[PLAYER DEBUG] Starting player detection process...")
             
             # Tolerância a falhas na nomenclatura do dicionário
             addr_id = self._addresses.get("id") or self._addresses.get("player_id")
             if not addr_id:
                 self._log.error("Chave 'id' ausente no dicionário PLAYER.")
                 return None

             # DEBUG: Log the address we're trying to read from
             self._log.debug(f"[PLAYER DEBUG] Attempting to read player ID from address: {hex(addr_id.value)}")
             
             # 1. Lê o ID
             player_id = self._memory.read_int(addr_id)
             
             self._log.debug(f"[PLAYER DEBUG] Read player ID: {player_id}")
             
             if player_id <= 0:
                 self._log.debug(f"Player ID {player_id}. Personagem offline.")
                 return None

             # 2. Leitura dos atributos vitais
             addr_hp = self._addresses.get("health", self._addresses.get("hp"))
             addr_hp_max = self._addresses.get("health_max", self._addresses.get("max_hp", addr_hp))
             addr_mana = self._addresses.get("mana", self._addresses.get("mp"))
             addr_mana_max = self._addresses.get("mana_max", self._addresses.get("max_mana", addr_mana))
             
             self._log.debug(f"[PLAYER DEBUG] Health addr: {hex(addr_hp.value) if addr_hp else 'None'}")
             self._log.debug(f"[PLAYER DEBUG] Health max addr: {hex(addr_hp_max.value) if addr_hp_max else 'None'}")
             self._log.debug(f"[PLAYER DEBUG] Mana addr: {hex(addr_mana.value) if addr_mana else 'None'}")
             self._log.debug(f"[PLAYER DEBUG] Mana max addr: {hex(addr_mana_max.value) if addr_mana_max else 'None'}")
             
             health = self._memory.read_int(addr_hp) if addr_hp else 0
             health_max = self._memory.read_int(addr_hp_max) if addr_hp_max else 0
             mana = self._memory.read_int(addr_mana) if addr_mana else 0
             mana_max = self._memory.read_int(addr_mana_max) if addr_mana_max else 0
             
             self._log.debug(f"[PLAYER DEBUG] Read values - Health: {health}/{health_max}, Mana: {mana}/{mana_max}")
             
             if mana < 0 or health < 0 or mana_max <= 0 or health_max <= 0:
                 self._log.debug(f"Valores vitais inconsistentes - Mana: {mana}, Health: {health}, Mana Max: {mana_max}, Health Max: {health_max} (Loading ou Offsets inválidos).")
                 return None
            
# 3. Leitura dos Status Gerais
             level = self._memory.read_int(self._addresses.get("level", addr_id))
             experience = self._memory.read_int(self._addresses.get("experience", addr_id))
             magic_level = self._memory.read_int(self._addresses.get("magic_level", addr_id))
             soul = self._memory.read_int(self._addresses.get("soul", addr_id))
             stamina = self._memory.read_int(self._addresses.get("stamina", addr_id))
             capacity = self._memory.read_int(self._addresses.get("capacity", addr_id))
             
             self._log.debug(f"[PLAYER DEBUG] Stats - Level: {level}, Experience: {experience}, Magic Level: {magic_level}")
             self._log.debug(f"[PLAYER DEBUG] Stats - Soul: {soul}, Stamina: {stamina}, Capacity: {capacity}")

             # 4. Leitura da Posição Absoluta (X, Y, Z)
             pos_x_addr = self._addresses.get("pos_x")
             pos_y_addr = self._addresses.get("pos_y")
             pos_z_addr = self._addresses.get("pos_z")
             
             self._log.debug(f"[PLAYER DEBUG] Position addresses - X: {hex(pos_x_addr.value) if pos_x_addr else 'None'}, Y: {hex(pos_y_addr.value) if pos_y_addr else 'None'}, Z: {hex(pos_z_addr.value) if pos_z_addr else 'None'}")
             
             # If position addresses are not configured, we cannot determine position
             if not all([pos_x_addr, pos_y_addr, pos_z_addr]):
                 self._log.warning("Position addresses not fully configured")
                 position = Position(x=0, y=0, z=0)  # Default position
             else:
                 try:
                     x = self._memory.read_int(pos_x_addr)
                     y = self._memory.read_int(pos_y_addr)
                     z = self._memory.read_int(pos_z_addr)
                     position = Position(x=x, y=y, z=z)
                     self._log.debug(f"[PLAYER DEBUG] Read position: ({x}, {y}, {z})")
                 except Exception as e:
                     self._log.debug(f"Could not read position: {e}")
                     position = Position(x=0, y=0, z=0)  # Default position on error
            
player_stats = Stats(
                 health=health,
                 max_health=health_max,
                 mana=mana,
                 max_mana=mana_max
             )
             
             # Read player name from memory
             addr_name = self._addresses.get("name")
             player_name = "Unknown"
             self._log.debug(f"[PLAYER DEBUG] Name address: {hex(addr_name.value) if addr_name else 'None'}")
             if addr_name:
                 try:
                     player_name = self._memory.read_string(addr_name, max_length=30)
                     self._log.debug(f"[PLAYER DEBUG] Raw name read: '{player_name}'")
                     # If name is empty or just whitespace, use a fallback
                     if not player_name or player_name.isspace():
                         player_name = f"Player_{player_id}"
                         self._log.debug(f"[PLAYER DEBUG] Name was empty/whitespace, using fallback: {player_name}")
                 except Exception as e:
                     self._log.debug(f"Could not read player name: {e}")
                     player_name = f"Player_{player_id}"
                     self._log.debug(f"[PLAYER DEBUG] Name read failed, using fallback: {player_name}")
             else:
                 # Fallback if name address not configured
                 player_name = f"Player_{player_id}"
                 self._log.debug(f"[PLAYER DEBUG] No name address configured, using fallback: {player_name}")

             self._log.debug(f"[PLAYER DEBUG] Final player name: '{player_name}'")

             player = Player(
                 id=player_id,
                 name=player_name,
                 position=position,
                 stats=player_stats, 
                 level=level,
                 experience=experience,
                 magic_level=magic_level,
                 soul=soul,
                 stamina=stamina,
                 capacity=capacity,
                 vocation="None"
             )

if "flags" in self._addresses:
                 flags = self._memory.read_int(self._addresses["flags"])
                 self._log.debug(f"[PLAYER DEBUG] Flags: {flags}")
                 if hasattr(player, "flags"):
                     player.flags = flags

             if "target_id" in self._addresses:
                 target_id = self._memory.read_int(self._addresses["target_id"])
                 self._log.debug(f"[PLAYER DEBUG] Target ID: {target_id}")
                 if hasattr(player, "target_id"):
                     player.target_id = target_id

             self._log.debug(f"[PLAYER DEBUG] Successfully created player object: ID={player.id}, Name='{player.name}', Level={player.level}, HP={player.stats.health}/{player.stats.max_health}")
             return player

        except MemoryReadError as e:
            # [ALTERAÇÃO] Rebaixado de WARNING para DEBUG. 
            # Evita poluição visual no terminal. O bot lidará com o 'None' silenciosamente.
            self._log.debug(f"Aguardando alocação de memória do jogo: {e}")
            return None
        except Exception as e:
            self._log.error(f"Erro inesperado no PlayerReader: {e}", exc_info=True)
            return None