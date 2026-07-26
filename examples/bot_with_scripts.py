"""
Exemplo de uso do bot com Script Engine (FASE 2).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position
from src.core.constants.addresses_860 import PLAYER, BATTLE_LIST, CREATURE
from src.infrastructure.logging.logger import get_logger, setup_logging


def main():
    # Configura logging para arquivo e console
    import os
    os.makedirs("logs", exist_ok=True)
    setup_logging(level="DEBUG", log_file="logs/bot_debug.log")
    logger = get_logger("Example")
    logger.info("=" * 60)
    logger.info("🎮 TIBIA BOT 8.60 - FASE 2 - SCRIPT ENGINE")
    logger.info("=" * 60)

    # Inicializa componentes
    pm = ProcessManager()
    memory_reader = MemoryReader(pm, cache_ttl=0.05)
    injector = KeyboardInjector(window_title_hint="Tibia")

    # Cria bot engine
    bot = BotEngine(pm, memory_reader, injector, PLAYER, BATTLE_LIST, CREATURE)

    if not bot.start():
        logger.error("Falha ao conectar. Certifique-se que o Tibia está aberto.")
        return

    # ========================================
    # REGISTRA SCRIPTS
    # ========================================
    
    # 1. Healing Script (prioridade máxima)
    healing = HealingScript()
    healing.config["hp_threshold"] = 60  # Cura quando HP < 60%
    healing.config["mana_threshold"] = 30
    bot.script_engine.register(healing)
    
    # 2. Aimbot Script
    aimbot = AimbotScript()
    aimbot.config["combat_mode"] = "lowest_hp"
    aimbot.config["max_distance"] = 7
    aimbot.config["target_blacklist"] = ["Training Assistant"]
    bot.script_engine.register(aimbot)
    
    # 3. Cavebot Script
    cavebot = CavebotScript()
    # Adiciona waypoints de exemplo
    cavebot.add_waypoint(Waypoint(Position(32360, 31780, 7), action="walk"))
    cavebot.add_waypoint(Waypoint(Position(32365, 31780, 7), action="walk"))
    cavebot.add_waypoint(Waypoint(Position(32365, 31785, 7), action="walk"))
    cavebot.add_waypoint(Waypoint(Position(32360, 31785, 7), action="walk"))
    cavebot.config["loop"] = True
    bot.script_engine.register(cavebot)
    
    # 4. Looter Script
    looter = LooterScript()
    looter.config["items_to_loot"] = {
        3031: "Gold Coin",
        3035: "Platinum Coin",
    }
    bot.script_engine.register(looter)

    # ========================================
    # CONFIGURA EVENT HANDLERS
    # ========================================
    
    handlers = EventHandlers()
    bot.event_manager.subscribe(EventType.PLAYER_HEALTH_LOW, handlers.on_health_low)
    bot.event_manager.subscribe(EventType.PLAYER_MANA_LOW, handlers.on_mana_low)
    bot.event_manager.subscribe(EventType.CREATURE_DETECTED, handlers.on_creature_detected)
    bot.event_manager.subscribe(EventType.LEVEL_UP, handlers.on_level_up)
    bot.event_manager.subscribe(EventType.CONNECTION_LOST, handlers.on_connection_lost)

    # ========================================
    # HABILITA SCRIPTS
    # ========================================
    
    logger.info("Habilitando scripts...")
    bot.script_engine.enable_script("HealingBot")
    bot.script_engine.enable_script("AimBot")
    bot.script_engine.enable_script("CaveBot")  # Descomente para ativar
    # bot.script_engine.enable_script("Looter")   # Descomente para ativar

    # Lista scripts
    logger.info("\nScripts registrados:")
    for script in bot.script_engine.list_scripts():
        status = "✓ ATIVO" if script["enabled"] else "✗ Inativo"
        logger.info(f"  {status} - {script['name']} (prioridade: {script['priority']})")

    # ========================================
    # INICIA BOT
    # ========================================
    
    bot.enabled = True
    logger.info("\n✓ Bot habilitado com Script Engine!")
    logger.info("Pressione Ctrl+C para parar.\n")

    try:
        bot.run_loop(interval=0.1)
    except KeyboardInterrupt:
        logger.info("\nInterrompido pelo usuário.")
    finally:
        bot.stop()
        logger.info("Bot encerrado.")


if __name__ == "__main__":
    main()
