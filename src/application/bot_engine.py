"""
BotEngine - núcleo do bot Tibia 8.60.
Gerencia loop principal, leitura de memória, scripts e eventos.
"""
from __future__ import annotations

import time
from typing import Optional, Dict, Any, List, Callable

from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.infrastructure.logging.logger import get_logger
from src.infrastructure.readers.player_reader import PlayerReader
from src.infrastructure.readers.creature_reader import CreatureReader

from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats

# Importa ScriptEngine já existente
from src.application.scripts.script_engine import ScriptEngine
from src.application.scripts.base_script import BaseScript


# ======================================================================
# Event Types
# ======================================================================
class EventType:
    """Tipos de eventos disparados pelo bot."""
    PLAYER_HEALTH_LOW = "PLAYER_HEALTH_LOW"
    PLAYER_MANA_LOW = "PLAYER_MANA_LOW"
    CREATURE_DETECTED = "CREATURE_DETECTED"
    LEVEL_UP = "LEVEL_UP"
    PLAYER_LOADED = "PLAYER_LOADED"
    CONNECTION_LOST = "CONNECTION_LOST"


# ======================================================================
# EventManager
# ======================================================================
class EventManager:
    """Gerenciador de eventos com publish/subscribe."""

    def __init__(self):
        self._log = get_logger("EventManager")
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Registra handler para um tipo de evento."""
        self._subscribers.setdefault(event_type, []).append(handler)
        self._log.debug(f"Handler registrado para {event_type}: {handler.__name__}")

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Remove handler de um tipo de evento."""
        if event_type in self._subscribers:
            self._subscribers[event_type] = [
                h for h in self._subscribers[event_type] if h != handler
            ]

    def publish(self, event_type: str, **kwargs) -> None:
        """Publica um evento para todos os handlers registrados."""
        handlers = self._subscribers.get(event_type, [])
        if not handlers:
            return

        for handler in handlers:
            try:
                handler(**kwargs)
            except Exception as e:
                self._log.error(f"Erro em handler de {event_type}: {e}", exc_info=True)


# ======================================================================
# BotEngine
# ======================================================================
class BotEngine:
    """
    Engine principal do bot.
    Responsável por:
      - Conectar ao processo Tibia
      - Ler estado do jogo (player, criaturas) via readers
      - Disparar eventos baseado em mudanças de estado
      - Executar scripts via ScriptEngine
    """

    def __init__(
        self,
        process_manager: ProcessManager,
        memory_reader: MemoryReader,
        keyboard_injector: KeyboardInjector,
        player_addresses: dict,
        battle_list_addresses: dict,
        creature_offsets: dict,
    ):
        self._log = get_logger("BotEngine")

        self._pm = process_manager
        self._memory = memory_reader
        self._injector = keyboard_injector

        # Inicializa readers com endereços
        self._player_reader = PlayerReader(self._memory, player_addresses)
        self._creature_reader = CreatureReader(
            self._memory, battle_list_addresses, creature_offsets
        )

        self.enabled: bool = False
        self.config: Dict[str, Any] = {
            "player_vocation": "Auto",
            "use_script_engine": True,
            "combat_mode": "lowest_hp",
        }

        # Estado atual
        self.player: Optional[Player] = None
        self.creatures: List[Creature] = []

        # Engine de scripts
        self.script_engine = ScriptEngine()

        # Event system
        self.event_manager = EventManager()

        # Snapshot anterior para detecção de eventos
        self._last_player: Optional[Player] = None
        self._last_creatures: List[Creature] = []

        self._connected: bool = False
        self._connection_retry_count: int = 0
        self._max_retry_attempts: int = 3

    # ------------------------------------------------------------------
    # Inicialização / conexão
    # ------------------------------------------------------------------
    def start(self) -> bool:
        """
        Conecta ao processo do Tibia e faz leitura inicial.
        Returns:
            True se conectado com sucesso.
        """
        try:
            # Conecta ao processo
            self._pm.attach()

            self._connected = True
            self._connection_retry_count = 0
            
            self._log.info("✓ Bot conectado ao processo Tibia.")
            self._log.info("✓ Memory Readers ativados (PlayerReader + CreatureReader).")
            self._log.info(f"✓ Script Engine pronto ({len(self.script_engine.list_scripts())} scripts).")
            self._log.info("⚠️  Auto-heal e Auto-attack DESABILITADOS por padrão (use bot.enabled = True).")

            return True

        except Exception as e:
            self._log.error(f"❌ Erro ao conectar ao Tibia: {e}", exc_info=True)
            self._connected = False
            return False

    def stop(self) -> None:
        """Desconecta e limpa estado."""
        self.enabled = False
        self._connected = False
        self._log.info("Bot parado.")

    # ------------------------------------------------------------------
    # Loop público
    # ------------------------------------------------------------------
    def tick(self) -> None:
        """
        Tick público chamado periodicamente pelo main loop.
        - Atualiza leitura de memória
        - Dispara eventos
        - Executa scripts se habilitado
        """
        if not self._connected:
            # Tenta reconectar
            if self._check_and_reconnect():
                self._log.info("✓ Reconectado com sucesso.")
            return

        # Atualiza estado
        self._update_state()

        # Processa eventos disparados por mudanças de estado
        self._process_events()

        # Executa scripts se bot habilitado
        if self.enabled and self.config.get("use_script_engine", True):
            self._run_scripts()

    def run_loop(self, interval: float = 0.1) -> None:
        """
        Loop interno opcional.
        Se você quer delegar o loop todo ao BotEngine.
        """
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

    # ------------------------------------------------------------------
    # Leitura de estado
    # ------------------------------------------------------------------
    def _update_state(self) -> None:
        """Atualiza player e criaturas usando os readers."""
        self._last_player = self.player
        self._last_creatures = self.creatures

        try:
            # Lê player
            self.player = self._player_reader.get_player()

            # Lê criaturas só se player está carregado
            if self.player:
                self.creatures = self._creature_reader.get_creatures()
            else:
                self.creatures = []

        except Exception as e:
            self._log.error(f"Erro ao atualizar estado: {e}", exc_info=True)
            self.player = None
            self.creatures = []

    def _check_and_reconnect(self) -> bool:
        """
        Verifica se ainda está conectado e tenta reconectar se perdeu.
        Returns:
            True se conectado (ou reconectou), False se falha.
        """
        try:
            # Tenta ler um valor simples como teste de conexão
            _ = self._memory.read_int(0x63FE8C)  # Player.Experience
            self._connection_retry_count = 0
            return True

        except Exception:
            self._connection_retry_count += 1

            if self._connection_retry_count >= self._max_retry_attempts:
                self._log.warning(
                    f"❌ Conexão perdida após {self._max_retry_attempts} tentativas."
                )
                self._connected = False
                self.event_manager.publish(EventType.CONNECTION_LOST)
                return False

            self._log.debug(f"Reconexão tentativa {self._connection_retry_count}...")
            return False

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _process_events(self) -> None:
        """
        Compara estado atual com anterior e dispara eventos.
        """
        if not self.player:
            return

        # Primeiro carregamento do player
        if self._last_player is None and self.player:
            self._log.info(f"✓ Player carregado: ID={self.player.id} HP={self.player.health}/{self.player.health_max}")
            self.event_manager.publish(EventType.PLAYER_LOADED, player=self.player)

        # HP baixo
        if self.player.hp_percent() < 30:
            self.event_manager.publish(EventType.PLAYER_HEALTH_LOW, player=self.player)

        # Mana baixa
        if self.player.mana_percent() < 20:
            self.event_manager.publish(EventType.PLAYER_MANA_LOW, player=self.player)

        # Level up
        if self._last_player and self.player.level > self._last_player.level:
            self._log.info(f"🎉 Level Up! {self.player.level - 1} → {self.player.level}")
            self.event_manager.publish(EventType.LEVEL_UP, player=self.player)

        # Novas criaturas apareceram
        last_ids = {c.id for c in (self._last_creatures or [])}
        for creature in self.creatures or []:
            if creature.id not in last_ids:
                self.event_manager.publish(
                    EventType.CREATURE_DETECTED,
                    creature=creature,
                    player=self.player,
                )

    # ------------------------------------------------------------------
    # Scripts
    # ------------------------------------------------------------------
    def _run_scripts(self) -> None:
        """Executa todos os scripts registrados via ScriptEngine."""
        context = {
            "player": self.player,
            "creatures": self.creatures,
            "bot_engine": self,
        }

        start_time = time.perf_counter()
        self.script_engine.execute_all(context)
        elapsed = time.perf_counter() - start_time

        # Avisa se scripts demoraram muito (target: <50ms)
        if elapsed > 0.05:
            self._log.debug(f"Scripts levaram {elapsed*1000:.1f}ms (target: <50ms)")
