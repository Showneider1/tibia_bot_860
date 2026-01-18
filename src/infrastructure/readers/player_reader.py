"""
Player Reader - Lê estado do player da memória.
Fonte: TibiaAPI 8.60 (https://github.com/ianobermiller/tibiaapi)
"""
from typing import Optional
from src.core.entities.player import Player
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.logging.logger import get_logger


class PlayerReader:
    """Lê dados do player diretamente da memória de forma otimizada."""

    def __init__(self, memory: MemoryReader, addresses: dict):
        """
        Args:
            memory: MemoryReader instance para leitura de memória
            addresses: Dicionário com endereços do player (ex: PLAYER dict de tibia_addresses.py)
        """
        self._memory = memory
        self._addresses = addresses
        self._log = get_logger("PlayerReader")
        self._last_valid_player: Optional[Player] = None

    def get_player(self) -> Optional[Player]:
        """
        Lê e retorna estado atual do player.
        
        Returns:
            Player object se conseguir ler, None se não conseguir ou player não está carregado.
        """
        try:
            # Lê ID do player como validação rápida
            player_id = self._memory.read_int(self._addresses["id"])
            
            # ID 0 significa player não carregado ou inválido
            if player_id == 0:
                return None

            # Se conseguiu ID, tenta ler todos os dados
            health = self._memory.read_int(self._addresses["health"])
            health_max = self._memory.read_int(self._addresses["health_max"])
            mana = self._memory.read_int(self._addresses["mana"])
            mana_max = self._memory.read_int(self._addresses["mana_max"])
            level = self._memory.read_int(self._addresses["level"])
            experience = self._memory.read_int(self._addresses["experience"])
            magic_level = self._memory.read_int(self._addresses["magic_level"])
            soul = self._memory.read_int(self._addresses["soul"])
            stamina = self._memory.read_int(self._addresses["stamina"])
            capacity = self._memory.read_int(self._addresses["capacity"])

            # Validação de sanidade nos valores
            if health < 0 or health_max < 0 or health > health_max:
                self._log.warning(f"Valores de health inválidos: {health}/{health_max}")
                return self._last_valid_player

            if mana < 0 or mana_max < 0 or mana > mana_max:
                self._log.warning(f"Valores de mana inválidos: {mana}/{mana_max}")
                return self._last_valid_player

            # Cria player com dados lidos
            player = Player(
                id=player_id,
                health=health,
                health_max=health_max,
                mana=mana,
                mana_max=mana_max,
                level=level,
                experience=experience,
                magic_level=magic_level,
                soul=soul,
                stamina=stamina,
                capacity=capacity,
            )

            # Armazena último player válido para fallback
            self._last_valid_player = player

            return player

        except Exception as e:
            self._log.error(f"Erro ao ler player: {e}", exc_info=True)
            # Retorna último estado válido conhecido
            return self._last_valid_player
