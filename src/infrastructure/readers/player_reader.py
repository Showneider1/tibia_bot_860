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
from src.core.constants.addresses_860 import VOCATIONS
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

            addr_id = self._addresses.get("id") or self._addresses.get("player_id")
            if not addr_id:
                self._log.error("Chave 'id' ausente no dicionário PLAYER.")
                return None

            self._log.debug(f"[PLAYER DEBUG] Reading player ID from: {hex(addr_id.value)}")
            player_id = self._memory.read_int(addr_id)
            self._log.debug(f"[PLAYER DEBUG] Player ID: {player_id}")

            if player_id <= 0:
                self._log.debug(f"Player ID {player_id} inválido. Personagem offline?")
                return None

            # --- Atributos vitais ---
            addr_hp      = self._addresses.get("health",     self._addresses.get("hp"))
            addr_hp_max  = self._addresses.get("health_max", self._addresses.get("max_hp", addr_hp))
            addr_mana    = self._addresses.get("mana",       self._addresses.get("mp"))
            addr_mana_max = self._addresses.get("mana_max",  self._addresses.get("max_mana", addr_mana))

            health      = self._memory.read_int(addr_hp)      if addr_hp      else 0
            health_max  = self._memory.read_int(addr_hp_max)  if addr_hp_max  else 0
            mana        = self._memory.read_int(addr_mana)    if addr_mana    else 0
            mana_max    = self._memory.read_int(addr_mana_max) if addr_mana_max else 0

            self._log.debug(f"[PLAYER DEBUG] HP: {health}/{health_max}, Mana: {mana}/{mana_max}")

            if health < 0 or health_max <= 0 or mana < 0 or mana_max <= 0:
                self._log.debug("Valores vitais inconsistentes. Personagem carregando?")
                return None

            # --- Stats gerais ---
            level        = self._memory.read_int(self._addresses.get("level",       addr_id))
            experience   = self._memory.read_int(self._addresses.get("experience",  addr_id))
            magic_level  = self._memory.read_int(self._addresses.get("magic_level", addr_id))
            soul         = self._memory.read_int(self._addresses.get("soul",        addr_id))
            stamina      = self._memory.read_int(self._addresses.get("stamina",     addr_id))
            capacity     = self._memory.read_int(self._addresses.get("capacity",    addr_id))

            self._log.debug(f"[PLAYER DEBUG] Level: {level}, Exp: {experience}, MagicLvl: {magic_level}")

            # --- Vocação dinâmica ---
            # Lê o byte de vocation da memória e mapeia para string.
            # Fallback para 'Unknown' se o valor não estiver no dicionário.
            vocation = "Unknown"
            addr_voc = self._addresses.get("vocation")
            if addr_voc:
                try:
                    voc_id = self._memory.read_int(addr_voc)
                    vocation = VOCATIONS.get(voc_id, f"Unknown({voc_id})")
                    self._log.debug(f"[PLAYER DEBUG] Vocation ID: {voc_id} -> '{vocation}'")
                except Exception as e:
                    self._log.debug(f"Não foi possível ler vocação: {e}")

            # --- Nome ---
            # Tenta ler da memória. Se falhar, usa fallback genérico.
            # O bot_engine depois sobrescreve com o nome real da BattleList.
            player_name = f"Player_{player_id}"
            addr_name = self._addresses.get("name")
            if addr_name:
                try:
                    raw = self._memory.read_string(addr_name, max_length=30)
                    if raw and not raw.isspace():
                        player_name = raw
                    self._log.debug(f"[PLAYER DEBUG] Name from memory: '{player_name}'")
                except Exception as e:
                    self._log.debug(f"Não foi possível ler nome: {e}")

            # --- Posição ---
            # Os endereços estáticos de pos_x/y/z não existem no OTClient.
            # A posição real SEMPRE virá do fallback no bot_engine (BattleList).
            # Usamos (0, 0, 0) como placeholder até o bot_engine corrigir.
            position = Position(x=0, y=0, z=0)

            # --- Monta o Player ---
            player = Player(
                id=player_id,
                name=player_name,
                position=position,
                stats=Stats(
                    health=health,
                    max_health=health_max,
                    mana=mana,
                    max_mana=mana_max,
                ),
                level=level,
                experience=experience,
                magic_level=magic_level,
                soul=soul,
                stamina=stamina,
                capacity=capacity,
                vocation=vocation,
            )

            # Flags opcionais
            if "flags" in self._addresses:
                try:
                    flags = self._memory.read_int(self._addresses["flags"])
                    if hasattr(player, "flags"):
                        player.flags = flags
                    self._log.debug(f"[PLAYER DEBUG] Flags: {flags}")
                except Exception:
                    pass

            self._log.debug(
                f"[PLAYER DEBUG] Player criado: ID={player.id}, Name='{player.name}', "
                f"Level={player.level}, Vocation='{player.vocation}', "
                f"HP={player.stats.health}/{player.stats.max_health}"
            )
            return player

        except MemoryReadError as e:
            self._log.debug(f"Aguardando alocação de memória do jogo: {e}")
            return None
        except Exception as e:
            self._log.error(f"Erro inesperado no PlayerReader: {e}", exc_info=True)
            return None
