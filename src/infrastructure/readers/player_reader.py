"""
Leitor de dados do Player na memoria do cliente Tibia.
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
    """Responsavel por extrair as informacoes do jogador da memoria."""

    def __init__(self, memory_reader: MemoryReader, addresses: Dict[str, MemoryAddress]):
        self._memory = memory_reader
        self._addresses = addresses
        self._log = get_logger("PlayerReader")

    def get_player(self) -> Optional[Player]:
        """Le os enderecos de memoria e constroi a entidade Player."""
        try:
            addr_id = self._addresses.get("id") or self._addresses.get("player_id")
            if not addr_id:
                self._log.error("Chave 'id' ausente no dicionario PLAYER.")
                return None

            player_id = self._memory.read_int(addr_id)
            if player_id <= 0:
                return None

            # Atributos vitais
            addr_hp       = self._addresses.get("health",    self._addresses.get("hp"))
            addr_hp_max   = self._addresses.get("health_max", self._addresses.get("max_hp", addr_hp))
            addr_mana     = self._addresses.get("mana",      self._addresses.get("mp"))
            addr_mana_max = self._addresses.get("mana_max",  self._addresses.get("max_mana", addr_mana))

            health     = self._memory.read_int(addr_hp)       if addr_hp       else 0
            health_max = self._memory.read_int(addr_hp_max)   if addr_hp_max   else 0
            mana       = self._memory.read_int(addr_mana)     if addr_mana     else 0
            mana_max   = self._memory.read_int(addr_mana_max) if addr_mana_max else 0

            if health < 0 or health_max <= 0 or mana < 0 or mana_max <= 0:
                return None

            # Stats gerais
            level       = self._memory.read_int(self._addresses.get("level",       addr_id))
            experience  = self._memory.read_int(self._addresses.get("experience",  addr_id))
            magic_level = self._memory.read_int(self._addresses.get("magic_level", addr_id))
            soul        = self._memory.read_int(self._addresses.get("soul",        addr_id))
            stamina     = self._memory.read_int(self._addresses.get("stamina",     addr_id))
            capacity    = self._memory.read_int(self._addresses.get("capacity",    addr_id))

            # Vocacao
            vocation = "Unknown"
            addr_voc = self._addresses.get("vocation")
            if addr_voc:
                try:
                    voc_id   = self._memory.read_int(addr_voc)
                    vocation = VOCATIONS.get(voc_id, f"Unknown({voc_id})")
                except Exception:
                    pass

            # Nome -- placeholder ate o bot_engine sincronizar com a BattleList
            # O bot_engine._update_state sobrescreve com o nome real da BattleList
            # assim que encontrar creature.id == player.id
            player_name = "Carregando..."
            addr_name = self._addresses.get("name")
            if addr_name:
                try:
                    raw = self._memory.read_string(addr_name, max_length=30)
                    if raw and raw.strip() and not raw.strip().isspace():
                        player_name = raw.strip()
                except Exception:
                    pass

            # Posicao inicial zerada -- sincronizada via BattleList no bot_engine
            position = Position(x=0, y=0, z=0)

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

            if "flags" in self._addresses:
                try:
                    flags = self._memory.read_int(self._addresses["flags"])
                    if hasattr(player, "flags"):
                        player.flags = flags
                except Exception:
                    pass

            self._log.debug(
                f"Player: ID={player.id} Name='{player.name}' "
                f"Level={player.level} Voc='{player.vocation}' "
                f"HP={player.stats.health}/{player.stats.max_health}"
            )
            return player

        except MemoryReadError as e:
            self._log.debug(f"Aguardando alocacao de memoria do jogo: {e}")
            return None
        except Exception as e:
            self._log.error(f"Erro inesperado no PlayerReader: {e}", exc_info=True)
            return None
