"""
BotEngine - nucleo do bot Tibia 8.60.
Gerencia loop principal, leitura de memoria, scripts e eventos.
"""
import time
from typing import Optional, Dict, Any, List

from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.infrastructure.logging.logger import get_logger

from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.address import MemoryAddress

from src.application.events.event_manager import EventManager
from src.application.events.event_types import EventType
from src.application.scripts.script_engine import ScriptEngine

from src.infrastructure.readers.player_reader import PlayerReader
from src.infrastructure.readers.creature_reader import CreatureReader

__all__ = ["BotEngine", "EventType", "EventManager"]


class BotEngine:
    """
    Engine principal do bot.

    Responsabilidades:
      - Conectar ao processo Tibia via ProcessManager
      - Ler dados do player e criaturas a cada tick
      - Disparar eventos (HP baixo, level up, criatura detectada...)
      - Executar scripts registrados no ScriptEngine

    Uso tipico:
        engine = BotEngine(pm, mr, ki, PLAYER, BATTLE_LIST, CREATURE)
        engine.start()
        while True:
            engine.tick()
            time.sleep(0.1)
    """

    # Numero de ticks consecutivos com HP/Mana baixo antes de re-emitir o evento.
    # Evita spam de eventos a cada tick quando o player esta com vida baixa.
    _HEALTH_EVENT_DEBOUNCE = 10
    _MAX_RETRY_ATTEMPTS = 5

    def __init__(
        self,
        process_manager: ProcessManager,
        memory_reader: MemoryReader,
        keyboard_injector: KeyboardInjector,
        player_addresses: Dict[str, Any],
        battle_list_addresses: Dict[str, Any],
        creature_offsets: Dict[str, int],
    ):
        self._log = get_logger("BotEngine")

        self._pm = process_manager
        self._memory = memory_reader
        self._injector = keyboard_injector

        self._player_reader = PlayerReader(self._memory, player_addresses)
        self._creature_reader = CreatureReader(self._memory, battle_list_addresses, creature_offsets)

        self.enabled: bool = False
        self.config: Dict[str, Any] = {
            "player_vocation": "Auto",
            "use_script_engine": True,
            "combat_mode": "lowest_hp",
        }

        self.player: Optional[Player] = None
        self.creatures: List[Creature] = []

        self.script_engine = ScriptEngine()
        self.event_manager = EventManager()

        self._last_player: Optional[Player] = None
        self._last_creatures: List[Creature] = []

        self._connected: bool = False

        # Contadores para reconexao e debounce de eventos
        self._connection_retry_count: int = 0
        self._health_low_ticks: int = 0
        self._mana_low_ticks: int = 0

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Conecta ao processo do Tibia e inicializa leitores."""
        try:
            if not self._pm.is_running():
                if not self._pm.attach():
                    self._log.error("Falha ao anexar ao processo Tibia.")
                    return False

            self._connected = True
            self._connection_retry_count = 0
            self._log.info("Bot conectado ao processo Tibia.")
            self._log.info(f"Script Engine pronto ({len(self.script_engine.list_scripts())} scripts).")
            self._log.info("Auto-heal e Auto-attack desabilitados por padrao (use bot.enabled = True).")
            return True

        except Exception as e:
            self._log.error(f"Erro ao conectar ao Tibia: {e}", exc_info=True)
            self._connected = False
            return False

    def stop(self) -> None:
        """Desconecta e limpa o estado."""
        self.enabled = False
        self._connected = False
        self._pm.detach()
        self._log.info("BotEngine parado.")

    def tick(self) -> None:
        """
        Executa um ciclo completo:
          1. Leitura de memoria
          2. Disparo de eventos
          3. Execucao de scripts (se habilitado)
        """
        if not self._connected:
            return

        start_time = time.perf_counter()

        self._update_state()
        self._process_events()

        if self.enabled and self.config.get("use_script_engine", True):
            self._run_scripts()

        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 50:
            self._log.debug(f"Tick lento: {elapsed:.1f}ms")

    def run_loop(self, interval: float = 0.1) -> None:
        """Loop autonomo — usa tick() internamente com controle de tempo."""
        self._log.info("BotEngine loop iniciado.")
        try:
            while True:
                start = time.perf_counter()
                self.tick()
                elapsed = time.perf_counter() - start
                time.sleep(max(0, interval - elapsed))
        except KeyboardInterrupt:
            self._log.info("Loop interrompido pelo usuario.")
        finally:
            self.stop()

    # ------------------------------------------------------------------
    # Leitura de estado (CORRIGIDO: metodo dentro da classe)
    # ------------------------------------------------------------------

    def _update_state(self) -> None:
        """
        Le a memoria do processo e atualiza self.player e self.creatures.

        Apos ler o player via PlayerReader, busca o player na lista de
        criaturas para sincronizar a posicao com maior precisao (a posicao
        na BattleList e mais confiavel que o endereco direto).
        """
        self._last_player = self.player
        self._last_creatures = list(self.creatures)

        try:
            self.player = self._player_reader.get_player()
            self.creatures = self._creature_reader.get_creatures()

            # Sincroniza posicao do player com a BattleList
            if self.player and self.creatures:
                for creature in self.creatures:
                    if creature.id == self.player.id:
                        self.player.position = creature.position
                        break

        except Exception as e:
            self._log.error(f"Erro ao atualizar estado: {e}", exc_info=True)

    def _check_and_reconnect(self) -> bool:
        """
        Testa a conexao lendo um endereco de referencia.
        Se falhar, incrementa o contador e tenta reconectar.

        Returns:
            True se a conexao esta ativa, False caso contrario.
        """
        try:
            self._memory.read_int(MemoryAddress(0x63FE8C), use_cache=False)
            self._connection_retry_count = 0
            return True
        except Exception:
            self._connection_retry_count += 1
            if self._connection_retry_count >= self._MAX_RETRY_ATTEMPTS:
                self._log.warning(
                    f"Conexao perdida apos {self._MAX_RETRY_ATTEMPTS} tentativas."
                )
                self._connected = False
                self.event_manager.emit(EventType.CONNECTION_LOST)
            else:
                self._log.debug(
                    f"Reconexao tentativa {self._connection_retry_count}/{self._MAX_RETRY_ATTEMPTS}..."
                )
            return False

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _process_events(self) -> None:
        """Compara o estado atual com o anterior e dispara eventos."""
        if not self.player:
            return

        # Primeiro carregamento
        if self._last_player is None:
            self._log.info(
                f"Player carregado: ID={self.player.id} "
                f"HP={self.player.stats.health}/{self.player.stats.max_health}"
            )
            self.event_manager.emit(EventType.PLAYER_LOADED, player=self.player)

        # HP baixo — com debounce para nao spammar
        if self.player.hp_percent() < 30:
            self._health_low_ticks += 1
            if self._health_low_ticks == 1 or self._health_low_ticks % self._HEALTH_EVENT_DEBOUNCE == 0:
                self.event_manager.emit(EventType.PLAYER_HEALTH_LOW, player=self.player)
        else:
            self._health_low_ticks = 0

        # Mana baixa — com debounce
        if self.player.mana_percent() < 20:
            self._mana_low_ticks += 1
            if self._mana_low_ticks == 1 or self._mana_low_ticks % self._HEALTH_EVENT_DEBOUNCE == 0:
                self.event_manager.emit(EventType.PLAYER_MANA_LOW, player=self.player)
        else:
            self._mana_low_ticks = 0

        # Level up
        if self._last_player and self.player.level > self._last_player.level:
            self._log.info(f"Level Up! {self._last_player.level} -> {self.player.level}")
            self.event_manager.emit(EventType.LEVEL_UP, player=self.player)

        # Novas criaturas
        last_ids = {c.id for c in self._last_creatures}
        for creature in self.creatures:
            if creature.id not in last_ids:
                self.event_manager.emit(
                    EventType.CREATURE_DETECTED,
                    creature=creature,
                    player=self.player,
                )

    # ------------------------------------------------------------------
    # Scripts
    # ------------------------------------------------------------------

    def _run_scripts(self) -> None:
        """Executa todos os scripts registrados com o contexto atual."""
        context = {
            "player": self.player,
            "creatures": self.creatures,
            "bot_engine": self,
        }
        self.script_engine.execute_all(context)
