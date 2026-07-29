"""
Leitor de dados do Player na memoria do cliente Tibia.

CORREÇÃO POSIÇÃO (BUG-POS-B):
  go_to_x/y/z (PLAYER_EXTRA) representa o destino do movimento interno do
  cliente, NÃO o tile atual do player. Em Tibia 8.60, a posição real fica
  nos offsets x/y/z da entrada do player na BattleList.

  Novo fluxo:
    1. Lê player_id de PLAYER["id"]
    2. Itera BattleList procurando slot com id == player_id
    3. Usa as coordenadas x/y/z desse slot como position
    4. Fallback para go_to_x/y/z se BattleList não encontrar o player

  CORREÇÃO API (BUG-POS-B2):
    MemoryAddress é um dataclass com atributo .value (não .address).
    read_int() recebe MemoryAddress diretamente; internamente chama
    _get_real_address(addr) que acessa addr.value.
    _get_position_from_battlelist() monta MemoryAddress(int) corretamente.
"""
from typing import Dict, Optional

from src.core.entities.player import Player
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats
from src.infrastructure.memory.memory_reader import MemoryReader
from src.core.value_objects.address import MemoryAddress
from src.core.exceptions.memory_exceptions import MemoryReadError
from src.core.constants.addresses_860 import VOCATIONS, BATTLE_LIST, CREATURE
from src.infrastructure.logging.logger import get_logger


class PlayerReader:
    """Responsavel por extrair as informacoes do jogador da memoria."""

    def __init__(self, memory_reader: MemoryReader, addresses: Dict[str, MemoryAddress]):
        self._memory = memory_reader
        self._addresses = addresses
        self._log = get_logger("PlayerReader")

    # ------------------------------------------------------------------
    # Posição via BattleList
    # ------------------------------------------------------------------

    def _get_position_from_battlelist(self, player_id: int) -> Optional[Position]:
        """
        Busca a posição real do player na BattleList.

        Tibia 8.60: a posição real (tile atual) está nos offsets
        CREATURE["x"]=36, CREATURE["y"]=40, CREATURE["z"]=44
        dentro do slot cuja id == player_id.

        MemoryAddress(int) é o construtor correto — o atributo do dataclass
        é .value, usado internamente por MemoryReader._get_real_address().
        """
        try:
            base_addr   = BATTLE_LIST["start"].value   # int: 0x63FEF8
            step        = BATTLE_LIST["step"]           # int: 0xA8
            max_entries = BATTLE_LIST["max_creatures"]  # int: 250

            off_id = CREATURE["id"]  # 0
            off_x  = CREATURE["x"]  # 36
            off_y  = CREATURE["y"]  # 40
            off_z  = CREATURE["z"]  # 44

            for i in range(max_entries):
                slot_base = base_addr + i * step

                slot_id = self._memory.read_int(
                    MemoryAddress(slot_base + off_id)
                )
                if slot_id != player_id:
                    continue

                # Encontrou o slot do player
                px = self._memory.read_int(MemoryAddress(slot_base + off_x))
                py = self._memory.read_int(MemoryAddress(slot_base + off_y))
                pz = self._memory.read_int(MemoryAddress(slot_base + off_z))

                if px > 0 and py > 0:
                    return Position(x=px, y=py, z=pz)

                return None  # slot encontrado mas coordenadas inválidas

        except Exception as e:
            self._log.debug(f"Falha ao ler posicao via BattleList: {e}")
        return None

    def _get_position_fallback(self) -> Position:
        """
        Fallback: lê go_to_x/y/z (PLAYER_EXTRA).
        Usado apenas se BattleList não retornar posição válida.
        """
        addr_gx = self._addresses.get("go_to_x")
        addr_gy = self._addresses.get("go_to_y")
        addr_gz = self._addresses.get("go_to_z")
        if addr_gx and addr_gy and addr_gz:
            try:
                px = self._memory.read_int(addr_gx, use_cache=False)
                py = self._memory.read_int(addr_gy, use_cache=False)
                pz = self._memory.read_int(addr_gz, use_cache=False)
                if px > 0 and py > 0:
                    return Position(x=px, y=py, z=pz)
            except Exception as e:
                self._log.debug(f"Falha ao ler go_to_x/y/z (fallback): {e}")
        return Position(x=0, y=0, z=0)

    # ------------------------------------------------------------------
    # Leitura principal
    # ------------------------------------------------------------------

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
            addr_hp_max   = self._addresses.get("health_max", self._addresses.get("max_hp"))
            addr_mana     = self._addresses.get("mana",      self._addresses.get("mp"))
            addr_mana_max = self._addresses.get("mana_max",  self._addresses.get("max_mana"))

            health     = self._memory.read_int(addr_hp)       if addr_hp       else 0
            health_max = self._memory.read_int(addr_hp_max)   if addr_hp_max   else 0
            mana       = self._memory.read_int(addr_mana)     if addr_mana     else 0
            mana_max   = self._memory.read_int(addr_mana_max) if addr_mana_max else 0

            if health < 0 or health_max <= 0 or mana < 0 or mana_max <= 0:
                return None

            # Stats gerais — fallback None (nao usar addr_id como fallback)
            addr_level   = self._addresses.get("level")
            addr_exp     = self._addresses.get("experience")
            addr_mlvl    = self._addresses.get("magic_level")
            addr_soul    = self._addresses.get("soul")
            addr_stamina = self._addresses.get("stamina")
            addr_cap     = self._addresses.get("capacity")

            level       = self._memory.read_int(addr_level)   if addr_level   else 0
            experience  = self._memory.read_int(addr_exp)     if addr_exp     else 0
            magic_level = self._memory.read_int(addr_mlvl)    if addr_mlvl    else 0
            soul        = self._memory.read_int(addr_soul)    if addr_soul    else 0
            stamina     = self._memory.read_int(addr_stamina) if addr_stamina else 0
            # FIXME: capacity address overlaps with name buffer (addresses_860.py)
            # Retorna 0 como fallback seguro ate endereco real ser calibrado via CE.
            try:
                capacity    = self._memory.read_int(addr_cap)     if addr_cap     else 0
            except Exception:
                capacity    = 0

            # Vocacao — lê 1 byte (read_int contamina com bytes adjacentes)
            vocation = "Unknown"
            addr_voc = self._addresses.get("vocation")
            if addr_voc:
                try:
                    voc_id   = self._memory.read_byte(addr_voc)
                    vocation = VOCATIONS.get(voc_id, f"Unknown({voc_id})")
                except Exception:
                    pass

            # Nome — placeholder ate bot_engine sincronizar com a BattleList
            player_name = "Carregando..."
            addr_name = self._addresses.get("name")
            if addr_name:
                try:
                    raw = self._memory.read_string(addr_name, max_length=30)
                    if raw and raw.strip() and not raw.strip().isspace():
                        player_name = raw.strip()
                except Exception:
                    pass

            # ----------------------------------------------------------
            # Posição: BattleList (fonte primária) → go_to_x/y/z (fallback)
            #
            # BUG-POS-B FIX: go_to_x/y/z é o destino do movimento do cliente,
            # não o tile atual. A posição real está na BattleList, slot cuja
            # id == player_id, offsets x=36 / y=40 / z=44.
            # ----------------------------------------------------------
            position = self._get_position_from_battlelist(player_id)
            if position is None:
                self._log.debug(
                    "Posicao via BattleList indisponivel; usando go_to_x/y/z como fallback."
                )
                position = self._get_position_fallback()

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
                f"HP={player.stats.health}/{player.stats.max_health} "
                f"Pos=({position.x},{position.y},{position.z})"
            )
            return player

        except MemoryReadError as e:
            self._log.debug(f"Aguardando alocacao de memoria do jogo: {e}")
            return None
        except Exception as e:
            self._log.error(f"Erro inesperado no PlayerReader: {e}", exc_info=True)
            return None
