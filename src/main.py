"""
Tibia Bot 8.60 - Main Entry Point
Bot inteligente com AI, Pathfinding e Script Engine.

Author: Your Name
Version: 1.0.0
"""
import sys
import time
import signal
from pathlib import Path

# Adiciona diretório raiz ao path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.application.bot_engine import BotEngine
from src.application.scripts.healing_script import HealingScript
from src.application.scripts.aimbot_script import AimbotScript
from src.application.scripts.cavebot_script import CavebotScript
from src.application.scripts.looter_script import LooterScript
from src.application.events.event_handlers import EventHandlers
from src.application.events.event_types import EventType
from src.config.settings import Settings
from src.utils.hotkeys import HotkeyManager
from src.infrastructure.logging.logger import setup_logging, get_logger


class TibiaBot:
    """Classe principal do bot."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        Inicializa o bot.
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        # Configurações
        self.settings = Settings(config_path)
        
        # Setup logging
        log_level = self.settings.get("logging.level", "INFO")
        log_file = self.settings.get("logging.file", "logs/bot.log")
        setup_logging(level=log_level, log_file=log_file)
        
        self._log = get_logger("TibiaBot")
        self._running = False
        
        # Componentes principais
        self.process_manager = None
        self.memory_reader = None
        self.keyboard_injector = None
        self.bot_engine = None
        self.hotkey_manager = HotkeyManager()
        
        # Scripts
        self._scripts = {}
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def initialize(self) -> bool:
        """
        Inicializa componentes do bot.
        
        Returns:
            True se inicializado com sucesso
        """
        self._log.info("=" * 70)
        self._log.info("🎮 TIBIA BOT 8.60 - STARTING")
        self._log.info("=" * 70)
        self._log.info(f"Version: {self.settings.get('bot.version', '1.0.0')}")
        self._log.info(f"Author: {self.settings.get('bot.author', 'Unknown')}")
        self._log.info("")
        
        try:
            # Inicializa Process Manager
            self._log.info("Inicializando Process Manager...")
            self.process_manager = ProcessManager()
            
            # Inicializa Memory Reader
            self._log.info("Inicializando Memory Reader...")
            cache_ttl = self.settings.get("memory.cache_ttl", 0.05)
            self.memory_reader = MemoryReader(self.process_manager, cache_ttl=cache_ttl)
            
            # Inicializa Keyboard Injector
            self._log.info("Inicializando Keyboard Injector...")
            window_title = self.settings.get("game.window_title", "Tibia")
            self.keyboard_injector = KeyboardInjector(window_title_hint=window_title)
            
            # Inicializa Bot Engine
            self._log.info("Inicializando Bot Engine...")
            self.bot_engine = BotEngine(
                self.process_manager,
                self.memory_reader,
                self.keyboard_injector
            )
            
            # Carrega configurações do player
            vocation = self.settings.get("player.vocation", "Auto")
            self.bot_engine.config["player_vocation"] = vocation
            self.bot_engine.config["use_script_engine"] = True
            
            # Conecta ao Tibia
            self._log.info("\nConectando ao Tibia...")
            if not self.bot_engine.start():
                self._log.error("❌ Falha ao conectar ao Tibia!")
                self._log.error("   Certifique-se que o jogo está aberto.")
                return False
            
            self._log.info("✓ Conectado ao Tibia com sucesso!")
            
            # Registra scripts
            self._register_scripts()
            
            # Registra event handlers
            self._register_event_handlers()
            
            # Registra hotkeys
            self._register_hotkeys()
            
            self._log.info("")
            self._log.info("=" * 70)
            self._log.info("✅ BOT INICIALIZADO COM SUCESSO")
            self._log.info("=" * 70)
            self._log.info("")
            
            return True
            
        except Exception as e:
            self._log.error(f"❌ Erro na inicialização: {e}", exc_info=True)
            return False
    
    def _register_scripts(self) -> None:
        """Registra e configura scripts."""
        self._log.info("\n📜 Registrando scripts...")
        
        # Healing Script
        if self.settings.get("scripts.healing.enabled", False):
            healing = HealingScript()
            healing.config.update({
                "hp_threshold": self.settings.get("scripts.healing.hp_threshold", 60),
                "mana_threshold": self.settings.get("scripts.healing.mana_threshold", 25),
                "spell_light": self.settings.get("scripts.healing.spell_light", "exura"),
                "spell_strong": self.settings.get("scripts.healing.spell_strong", "exura gran"),
                "spell_ultimate": self.settings.get("scripts.healing.spell_ultimate", "exura vita"),
            })
            self.bot_engine.script_engine.register(healing)
            self.bot_engine.script_engine.enable_script("HealingBot")
            self._scripts["healing"] = healing
            self._log.info(f"  ✓ HealingBot (threshold: {healing.config['hp_threshold']}%)")
        
        # Aimbot Script
        if self.settings.get("scripts.aimbot.enabled", False):
            aimbot = AimbotScript()
            aimbot.config.update({
                "max_distance": self.settings.get("scripts.aimbot.max_distance", 7),
                "attack_hotkey": self.settings.get("scripts.aimbot.attack_hotkey", "F1"),
                "min_hp_to_attack": self.settings.get("scripts.aimbot.min_hp_to_attack", 40),
                "use_combat_ai": self.settings.get("scripts.aimbot.use_combat_ai", True),
                "target_blacklist": self.settings.get("scripts.aimbot.blacklist", []),
            })
            self.bot_engine.script_engine.register(aimbot)
            self.bot_engine.script_engine.enable_script("AimBot")
            self._scripts["aimbot"] = aimbot
            self._log.info(f"  ✓ AimBot (max_dist: {aimbot.config['max_distance']} SQM)")
        
        # Cavebot Script
        if self.settings.get("scripts.cavebot.enabled", False):
            cavebot = CavebotScript()
            cavebot.config.update({
                "loop": self.settings.get("scripts.cavebot.loop", True),
                "use_pathfinding": self.settings.get("scripts.cavebot.use_pathfinding", True),
                "waypoints": self.settings.get("scripts.cavebot.waypoints", []),
            })
            self.bot_engine.script_engine.register(cavebot)
            self.bot_engine.script_engine.enable_script("CaveBot")
            self._scripts["cavebot"] = cavebot
            self._log.info(f"  ✓ CaveBot (waypoints: {len(cavebot.config['waypoints'])})")
        
        # Looter Script
        if self.settings.get("scripts.looter.enabled", False):
            looter = LooterScript()
            looter.config.update({
                "loot_radius": self.settings.get("scripts.looter.loot_radius", 1),
                "open_corpses": self.settings.get("scripts.looter.open_corpses", True),
                "loot_items": self.settings.get("scripts.looter.items", {}),
            })
            self.bot_engine.script_engine.register(looter)
            self.bot_engine.script_engine.enable_script("Looter")
            self._scripts["looter"] = looter
            self._log.info(f"  ✓ Looter ({len(looter.config['loot_items'])} items)")
        
        if not self._scripts:
            self._log.warning("  ⚠️  Nenhum script habilitado no config.yaml")
    
    def _register_event_handlers(self) -> None:
        """Registra handlers de eventos."""
        self._log.info("\n📡 Registrando event handlers...")
        
        handlers = EventHandlers()
        
        # Registra eventos padrão
        self.bot_engine.event_manager.subscribe(EventType.PLAYER_HEALTH_LOW, handlers.on_health_low)
        self.bot_engine.event_manager.subscribe(EventType.PLAYER_MANA_LOW, handlers.on_mana_low)
        self.bot_engine.event_manager.subscribe(EventType.CREATURE_DETECTED, handlers.on_creature_detected)
        self.bot_engine.event_manager.subscribe(EventType.LEVEL_UP, handlers.on_level_up)
        
        self._log.info("  ✓ Event handlers registrados")
    
    def _register_hotkeys(self) -> None:
        """Registra hotkeys globais."""
        self._log.info("\n⌨️  Registrando hotkeys...")
        
        # Hotkey para habilitar/desabilitar bot
        enable_key = self.settings.get("hotkeys.enable_bot", "Insert")
        self.hotkey_manager.register(enable_key, self._toggle_bot)
        self._log.info(f"  ✓ Toggle Bot: {enable_key}")
        
        # Hotkey para parada de emergência
        emergency_key = self.settings.get("hotkeys.emergency_stop", "End")
        self.hotkey_manager.register(emergency_key, self._emergency_stop)
        self._log.info(f"  ✓ Emergency Stop: {emergency_key}")
    
    def _toggle_bot(self) -> None:
        """Toggle do estado do bot (ativado/desativado)."""
        if self.bot_engine:
            self.bot_engine.enabled = not self.bot_engine.enabled
            status = "HABILITADO" if self.bot_engine.enabled else "DESABILITADO"
            self._log.info(f"🔄 Bot {status}")
    
    def _emergency_stop(self) -> None:
        """Parada de emergência."""
        self._log.warning("🚨 PARADA DE EMERGÊNCIA ACIONADA!")
        self._running = False
    
    def _signal_handler(self, signum, frame) -> None:
        """Handler para sinais do sistema."""
        self._log.info("\n⚠️  Sinal de interrupção recebido. Encerrando...")
        self._running = False
    
    def run(self) -> None:
        """Loop principal do bot."""
        if not self.bot_engine:
            self._log.error("Bot não inicializado! Chame initialize() primeiro.")
            return
        
        self._running = True
        
        # Instruções para o usuário
        self._log.info("🎮 BOT EM EXECUÇÃO")
        self._log.info("")
        self._log.info("Comandos:")
        enable_key = self.settings.get("hotkeys.enable_bot", "Insert")
        emergency_key = self.settings.get("hotkeys.emergency_stop", "End")
        self._log.info(f"  [{enable_key}] - Habilitar/Desabilitar bot")
        self._log.info(f"  [{emergency_key}] - Parada de emergência")
        self._log.info("  [Ctrl+C] - Encerrar")
        self._log.info("")
        self._log.info("Pressione Insert para HABILITAR o bot...")
        self._log.info("")
        
        try:
            # Loop principal
            loop_interval = 0.1  # 100ms
            
            while self._running:
                start_time = time.perf_counter()
                
                # Executa tick do bot
                if self.bot_engine.enabled:
                    try:
                        self.bot_engine.tick()
                    except Exception as e:
                        self._log.error(f"Erro no tick: {e}", exc_info=True)
                
                # Aguarda próximo tick
                elapsed = time.perf_counter() - start_time
                sleep_time = max(0, loop_interval - elapsed)
                time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            self._log.info("\n⚠️  Interrompido pelo usuário.")
        except Exception as e:
            self._log.error(f"\n❌ Erro fatal: {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def shutdown(self) -> None:
        """Encerra o bot gracefully."""
        self._log.info("\n" + "=" * 70)
        self._log.info("ENCERRANDO BOT")
        self._log.info("=" * 70)
        
        try:
            # Remove hotkeys
            if self.hotkey_manager:
                self._log.info("Removendo hotkeys...")
                self.hotkey_manager.unregister_all()
            
            # Para bot engine
            if self.bot_engine:
                self._log.info("Parando Bot Engine...")
                self.bot_engine.stop()
            
            # Salva configurações
            self._log.info("Salvando configurações...")
            self.settings.save()
            
            self._log.info("=" * 70)
            self._log.info("✅ BOT ENCERRADO COM SUCESSO")
            self._log.info("=" * 70)
            
        except Exception as e:
            self._log.error(f"Erro no shutdown: {e}", exc_info=True)


def main():
    print("...banner...")
    config_file = "config.local.yaml" if Path("config.local.yaml").exists() else "config.yaml"
    bot = TibiaBot(config_path=config_file)

    if bot.initialize():
        bot.run()
    else:
        print("\n❌ Falha na inicialização. Verifique os logs.")
        input("\nPressione ENTER para sair...")
        sys.exit(1)


if __name__ == "__main__":
    main()
