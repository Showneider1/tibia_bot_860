"""
Main - Entry point do bot Tibia 8.60.
"""
import time
import sys
from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.infrastructure.logging.logger import get_logger

from src.application.bot_engine import BotEngine, EventType

# Importa endereços oficiais da TibiaAPI
from src.infrastructure.tibia_addresses import (
    PLAYER,
    BATTLE_LIST,
    CREATURE,
)


class BotApplication:
    """Aplicação principal do bot."""

    def __init__(self):
        self._log = get_logger("BotApplication")
        self.bot_engine: BotEngine | None = None

    def initialize(self) -> bool:
        """Inicializa todos os componentes do bot."""
        try:
            self._log.info("=" * 60)
            self._log.info("🤖 TIBIA BOT 8.60 - Inicializando...")
            self._log.info("=" * 60)

            # Cria componentes de infraestrutura
            process_manager = ProcessManager()
            memory_reader = MemoryReader(process_manager)
            keyboard_injector = KeyboardInjector(process_manager)

            # Cria BotEngine com endereços da TibiaAPI
            self.bot_engine = BotEngine(
                process_manager=process_manager,
                memory_reader=memory_reader,
                keyboard_injector=keyboard_injector,
                player_addresses=PLAYER,
                battle_list_addresses=BATTLE_LIST,
                creature_offsets=CREATURE,
            )

            # Registra handlers de eventos
            self._setup_event_handlers()

            # Conecta ao Tibia
            if not self.bot_engine.start():
                self._log.error("❌ Falha ao conectar ao Tibia.")
                return False

            return True

        except Exception as e:
            self._log.error(f"❌ Erro ao inicializar bot: {e}", exc_info=True)
            return False

    def _setup_event_handlers(self) -> None:
        """Registra handlers de eventos."""
        self.bot_engine.event_manager.subscribe(
            EventType.PLAYER_LOADED,
            self._on_player_loaded
        )
        self.bot_engine.event_manager.subscribe(
            EventType.PLAYER_HEALTH_LOW,
            self._on_player_health_low
        )
        self.bot_engine.event_manager.subscribe(
            EventType.CREATURE_DETECTED,
            self._on_creature_detected
        )
        self.bot_engine.event_manager.subscribe(
            EventType.CONNECTION_LOST,
            self._on_connection_lost
        )

    def _on_player_loaded(self, player, **kwargs):
        """Disparado quando player é carregado."""
        self._log.info(f"✓ Player carregado: {player.id}")

    def _on_player_health_low(self, player, **kwargs):
        """Disparado quando HP está baixo."""
        self._log.warning(f"⚠️  HP BAIXO: {player.health}/{player.health_max} ({player.hp_percent():.0f}%)")

    def _on_creature_detected(self, creature, player, **kwargs):
        """Disparado quando criatura é detectada."""
        self._log.info(f"👹 Criatura detectada: {creature.name} (ID: {creature.id})")

    def _on_connection_lost(self, **kwargs):
        """Disparado quando perde conexão com o cliente."""
        self._log.error("❌ Conexão perdida com o cliente Tibia!")

    def run(self, tick_interval: float = 0.1) -> None:
        """Loop principal do bot."""
        self._log.info("\n" + "=" * 60)
        self._log.info("🚀 Bot iniciado. Pressione Ctrl+C para parar.")
        self._log.info("=" * 60 + "\n")

        try:
            while True:
                start = time.perf_counter()

                # Executa um tick
                self.bot_engine.tick()

                # Controla frame rate
                elapsed = time.perf_counter() - start
                time.sleep(max(0, tick_interval - elapsed))

        except KeyboardInterrupt:
            self._log.info("\n⏹️  Bot parado pelo usuário.")
        except Exception as e:
            self._log.error(f"❌ Erro no loop principal: {e}", exc_info=True)
        finally:
            self.bot_engine.stop()

    def run_interactive(self) -> None:
        """Loop com interação por comandos."""
        self._log.info("\n" + "=" * 60)
        self._log.info("🚀 Bot em modo interativo.")
        self._log.info("Comandos: 'start', 'stop', 'status', 'exit'")
        self._log.info("=" * 60 + "\n")

        try:
            while True:
                cmd = input(">>> ").strip().lower()

                if cmd == "start":
                    self.bot_engine.enabled = True
                    self._log.info("✓ Bot habilitado.")

                elif cmd == "stop":
                    self.bot_engine.enabled = False
                    self._log.info("✓ Bot desabilitado.")

                elif cmd == "status":
                    player_info = (
                        f"ID={self.bot_engine.player.id}, "
                        f"HP={self.bot_engine.player.health}/{self.bot_engine.player.health_max}, "
                        f"Mana={self.bot_engine.player.mana}/{self.bot_engine.player.mana_max}"
                        if self.bot_engine.player
                        else "Player não carregado"
                    )
                    creature_count = len(self.bot_engine.creatures)
                    self._log.info(f"Player: {player_info}")
                    self._log.info(f"Criaturas: {creature_count}")
                    self._log.info(f"Scripts registrados: {len(self.bot_engine.script_engine.list_scripts())}")

                elif cmd == "exit":
                    break

                else:
                    self._log.info("❓ Comando inválido.")

                # Faz um tick do bot
                self.bot_engine.tick()
                time.sleep(0.05)

        except KeyboardInterrupt:
            self._log.info("\n⏹️  Saindo...")
        finally:
            self.bot_engine.stop()


def main():
    """Entry point."""
    app = BotApplication()

    if not app.initialize():
        sys.exit(1)

    # Escolha modo: automático ou interativo
    # app.run()  # Modo automático
    app.run_interactive()  # Modo interativo (recomendado para debug)


if __name__ == "__main__":
    main()
