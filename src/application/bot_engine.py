"""
BotEngine - núcleo do bot Tibia 8.60.
Gerencia loop principal, leitura de memória, scripts e eventos.
"""
import time
from typing import Optional, Dict, Any, List

from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.infrastructure.logging.logger import get_logger

from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats

from src.application.scripts.script_engine import ScriptEngine
from src.application.events.event_manager import EventManager
from src.application.events.event_types import EventType

from src.infrastructure.readers.player_reader import PlayerReader
from src.infrastructure.readers.creature_reader import CreatureReader

class BotEngine:
    """
    Engine principal do bot.
    Responsável por conectar ao processo, ler a memória e executar o ScriptEngine.
    """

    def __init__(
        self,
        process_manager: ProcessManager,
        memory_reader: MemoryReader,
        keyboard_injector: KeyboardInjector,
        player_addresses: Dict[str, Any],
        battle_list_addresses: Dict[str, Any],
        creature_offsets: Dict[str, int]
    ):
        self._log = get_logger("BotEngine")

        self._pm = process_manager
        self._memory = memory_reader
        self._injector = keyboard_injector

        # Inicializa os leitores reais de memória
        self._player_reader = PlayerReader(self._memory, player_addresses)
        self._creature_reader = CreatureReader(self._memory, battle_list_addresses, creature_offsets)

        self.enabled: bool = False
        self.config: Dict[str, Any] = {
            "player_vocation": "Auto",
            "use_script_engine": True,
            "combat_mode": "lowest_hp",
        }

        # Estado atual
        self.player: Optional[Player] = None
        self.creatures: List[Creature] = []

        # Sistemas de Scripts e Eventos
        self.script_engine = ScriptEngine()
        self.event_manager = EventManager()

        # Snapshot anterior para detecção de eventos
        self._last_player: Optional[Player] = None
        self._last_creatures: List[Creature] = []

        self._connected: bool = False

    def start(self) -> bool:
        """Conecta ao processo do Tibia e faz leitura inicial."""
        try:
            if not self._pm.is_running():
                self._pm.attach()

            self._connected = True
            self._log.info("✓ Bot conectado ao processo Tibia.")
            self._log.info("✓ Memory Readers ativados (PlayerReader + CreatureReader).")
            self._log.info(f"✓ Script Engine pronto ({len(self.script_engine.list_scripts())} scripts).")
            self._log.info("⚠️  Auto-heal e Auto-attack DESABILITADOS por padrão (use bot.enabled = True).")

            return True
        except Exception as e:
            self._log.error(f"Erro ao conectar ao Tibia: {e}", exc_info=True)
            self._connected = False
            return False

    def stop(self) -> None:
        """Desconecta e limpa o estado."""
        self.enabled = False
        self._connected = False
        self._log.info("BotEngine parado.")

    def tick(self) -> None:
        """Tick do main loop. Lê a memória e corre os scripts."""
        if not self._connected:
            return

        start_time = time.perf_counter()
        
        # 1. Atualiza leitura de memória
        self._update_state()

        # 2. Dispara eventos
        self._process_events()

        # 3. Executa scripts se o bot estiver habilitado
        if self.enabled and self.config.get("use_script_engine", True):
            self._run_scripts()
        
        elapsed = (time.perf_counter() - start_time) * 1000
        # Opcional: Loga se o ciclo demorar mais do que o esperado
        if elapsed > 50:
             self._log.debug(f"Scripts levaram {elapsed:.1f}ms (target: <50ms)")

    def run_loop(self, interval: float = 0.1) -> None:
        """Loop interno, caso pretenda delegar o controlo de tempo ao BotEngine."""
        self._log.info("BotEngine loop iniciado.")
        try:
            while True:
                start = time.perf_counter()
                self.tick()
                elapsed = time.perf_counter() - start
                time.sleep(max(0, interval - elapsed))
        except KeyboardInterrupt:
            self._log.info("Loop interrompido pelo usuário.")
        finally:
            self.stop()

    def _update_state(self) -> None:
        """Lê a memória e sincroniza a posição real da BattleList."""
        self._last_player = self.player
        self._last_creatures = self.creatures

        try:
            # Lê a entidade Player e todas as criaturas no ecrã
            self.player = self._player_reader.get_player()
            self.creatures = self._creature_reader.get_creatures()

            # =========================================================
            # CORREÇÃO DA POSIÇÃO (Sincronização com a BattleList)
            # =========================================================
            # Como o goto_x não é exato, procuramos o nosso char na lista
            # de criaturas para roubar as coordenadas físicas perfeitas!
            if self.player and self.creatures:
                for creature in self.creatures:
                    if creature.id == self.player.id:
                        self.player.position = creature.position
                        self.player.name = creature.name
                        break

        except Exception as e:
            self._log.error(f"Erro ao atualizar estado: {e}", exc_info=True)

    def _process_events(self) -> None:
        """Verifica alterações e dispara eventos."""
        if not self.player:
            return

        # Log de carregamento inicial
        if not self._last_player:
            self._log.info(f"✓ Player carregado: ID={self.player.id} HP={self.player.stats.health}/{self.player.stats.max_health}")

        try:
            # Cálculos de percentagem usando os Stats
            hp_pct = (self.player.stats.health / self.player.stats.max_health) * 100 if self.player.stats.max_health > 0 else 100
            mana_pct = (self.player.stats.mana / self.player.stats.max_mana) * 100 if self.player.stats.max_mana > 0 else 100

            if hp_pct < 30:
                self.event_manager.publish(EventType.PLAYER_HEALTH_LOW, player=self.player)

            if mana_pct < 20:
                self.event_manager.publish(EventType.PLAYER_MANA_LOW, player=self.player)

            if self._last_player and self.player.level > self._last_player.level:
                self.event_manager.publish(EventType.LEVEL_UP, player=self.player)

            # Novas criaturas no ecrã
            last_ids = {c.id for c in (self._last_creatures or [])}
            for creature in self.creatures or []:
                if creature.id not in last_ids:
                    self.event_manager.publish(
                        EventType.CREATURE_DETECTED,
                        creature=creature,
                        player=self.player,
                    )
        except Exception as e:
            self._log.error(f"Erro ao processar eventos: {e}")

    def _run_scripts(self) -> None:
        """Corre os scripts e injeta o contexto."""
        context = {
            "player": self.player,
            "creatures": self.creatures,
            "bot_engine": self,
        }
        self.script_engine.execute_all(context)