"""
Leitor de dados do Player na memória do cliente Tibia.
"""
from typing import Dict, Optional
from src.core.entities.player import Player
from src.core.value_objects.stats import Stats
from src.core.value_objects.position import Position
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
            # 1. Lê o ID primeiro para verificar se o jogador está logado
            player_id = self._memory.read_int(self._addresses["id"])
            
            # Se o ID for 0 (ou muito pequeno), o personagem não está logado
            if player_id <= 0:
                return None

            # 2. Leitura dos atributos de Vida e Mana
            health = self._memory.read_int(self._addresses["health"])
            health_max = self._memory.read_int(self._addresses["health_max"])
            mana = self._memory.read_int(self._addresses["mana"])
            mana_max = self._memory.read_int(self._addresses["mana_max"])
            
            # 3. Leitura dos Status Gerais
            level = self._memory.read_int(self._addresses["level"])
            experience = self._memory.read_int(self._addresses["experience"])
            magic_level = self._memory.read_int(self._addresses["magic_level"])
            soul = self._memory.read_int(self._addresses["soul"])
            stamina = self._memory.read_int(self._addresses["stamina"])
            capacity = self._memory.read_int(self._addresses["capacity"])

            # 4. Leitura da Posição Absoluta (X, Y, Z)
            x = self._memory.read_int(self._addresses["pos_x"])
            y = self._memory.read_int(self._addresses["pos_y"])
            z = self._memory.read_int(self._addresses["pos_z"])
            position = Position(x, y, z)
            
            # Cria o objeto de Valor (Value Object) Stats
            player_stats = Stats(
                health=health,
                max_health=health_max,
                mana=mana,
                max_mana=mana_max
            )

            # Passa o 'player_stats' encapsulado para o construtor do Player
            player = Player(
                id=player_id,
                name="Self",
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

            return player

        except MemoryReadError as e:
            # Captura erros de leitura caso o processo feche de repente
            self._log.error(f"Erro ao ler memória do player: {e}")
            return None
        except Exception as e:
            self._log.error(f"Erro inesperado no PlayerReader: {e}", exc_info=True)
            return None