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

from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats

# usa o ScriptEngine que você já tem em src/application/scripts/script_engine.py
from src.application.scripts.script_engine import ScriptEngine
from src.application.scripts.base_script import BaseScript


# ======================================================================
# Event Types (se já tiver um arquivo separado, pode remover esta parte)
# ======================================================================
class EventType:
    PLAYER_HEALTH_LOW = "PLAYER_HEALTH_LOW"
    PLAYER_MANA_LOW = "PLAYER_MANA_LOW"
    CREATURE_DETECTED = "CREATURE_DETECTED"
    LEVEL_UP = "LEVEL_UP"


# ======================================================================
# EventManager simples
# ======================================================================
class EventManager:
    """Gerenciador simples de eventos (publish/subscribe)."""

    def __init__(self):
        self._log = get_logger("EventManager")
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)
        self._log.debug(f"Handler registrado para {event_type}: {handler.__name__}")

    def publish(self, event_type: str, **kwargs) -> None:
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
      - Ler estado do jogo (player, criaturas)
      - Disparar eventos
      - Executar scripts via ScriptEngine
    """

    def __init__(
        self,
        process_manager: ProcessManager,
        memory_reader: MemoryReader,
        keyboard_injector: KeyboardInjector,
    ):
        self._log = get_logger("BotEngine")

        self._pm = process_manager
        self._memory = memory_reader
        self._injector = keyboard_injector

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
            # Garante que o process manager está apontando para o cliente
            self._pm.attach()

            self._connected = True
            self._log.info("Bot conectado ao processo.")
            self._log.info("⚠️  Auto-heal e Auto-attack DESABILITADOS por padrão.")
            self._log.info("✓ Script Engine ativo.")
            self._log.info(f"  {len(self.script_engine.list_scripts())} scripts registrados.")

            return True
        except Exception as e:
            self._log.error(f"Erro ao conectar ao Tibia: {e}", exc_info=True)
            self._connected = False
            return False

    def stop(self) -> None:
        """Desconecta e limpa estado."""
        self.enabled = False
        self._connected = False
        self._log.info("BotEngine parado.")

    # ------------------------------------------------------------------
    # Loop público
    # ------------------------------------------------------------------
    def tick(self) -> None:
        """
        Tick público. Deve ser chamado periodicamente pelo main loop.
        Se o bot estiver desabilitado, apenas atualiza estado/eventos.
        """
        if not self._connected:
            return

        # Atualiza leitura de memória
        self._update_state()

        # Dispara eventos
        self._process_events()

        # Executa scripts se o bot estiver habilitado
        if self.enabled and self.config.get("use_script_engine", True):
            self._run_scripts()

    def run_loop(self, interval: float = 0.1) -> None:
        """
        Loop interno opcional, caso queira delegar o loop ao BotEngine.
        """
        self._log.info("BotEngine loop iniciado.")
        try:
            while True:
                start = time.perf_counter()
                self.tick()
                elapsed = time.perf_counter() - start
                time.sleep(max(0, interval - elapsed))
        except KeyboardInterrupt:
            self._log.info("Loop do BotEngine interrompido pelo usuário.")
        finally:
            self.stop()

    # ------------------------------------------------------------------
    # Leitura de estado
    # ------------------------------------------------------------------
    def _update_state(self) -> None:
        """Atualiza player e criaturas a partir da memória."""
        self._last_player = self.player
        self._last_creatures = self.creatures

        try:
            # Aqui você pluga seu código real de leitura.
            # Vou deixar um stub seguro para não quebrar.

            # Se você já tem readers específicos, descomente e ajuste:
            # from src.infrastructure.services.player_reader import PlayerReader
            # from src.infrastructure.services.creature_reader import CreatureReader
            #
            # player_reader = PlayerReader(self._memory)
            # creature_reader = CreatureReader(self._memory)
            #
            # self.player = player_reader.get_player()
            # self.creatures = creature_reader.get_creatures()

            # Se ainda não tem readers, mantenha player/creatures como estão.
            if self.player is None:
                # Evita flood de log; loga só uma vez
                self._log.debug("Player ainda não carregado (implementação de reader pendente).")

        except Exception as e:
            self._log.error(f"Erro ao atualizar estado: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------
    def _process_events(self) -> None:
        """Compara estado atual com anterior e dispara eventos."""
        if not self.player:
            return

        # HP baixo
        if self.player.hp_percent() < 30:
            self.event_manager.publish(EventType.PLAYER_HEALTH_LOW, player=self.player)

        # Mana baixa
        if self.player.mana_percent() < 20:
            self.event_manager.publish(EventType.PLAYER_MANA_LOW, player=self.player)

        # Level up
        if self._last_player and self.player.level > self._last_player.level:
            self.event_manager.publish(EventType.LEVEL_UP, player=self.player)

        # Novas criaturas
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
        # Usa o método do ScriptEngine que você já tem:
        self.script_engine.execute_all(context)
