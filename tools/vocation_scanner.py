"""
Teste completo da FASE 2 - Script Engine + Events.
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
from src.application.events.event_handlers import EventHandlers
from src.application.events.event_types import EventType
from src.infrastructure.logging.logger import get_logger


def main():
    logger = get_logger("TestPhase2")
    logger.info("=" * 70)
    logger.info("🧪 TESTE FASE 2 - SCRIPT ENGINE + EVENTS")
    logger.info("=" * 70)

    # ========================================
    # SETUP
    # ========================================
    pm = ProcessManager()
    memory_reader = MemoryReader(pm, cache_ttl=0.05)
    injector = KeyboardInjector(window_title_hint="Tibia")

    bot = BotEngine(pm, memory_reader, injector)

    if not bot.start():
        logger.error("❌ Falha ao conectar ao Tibia.")
        return

    # ========================================
    # CONFIGURAÇÃO DO BOT
    # ========================================
    bot.config["player_vocation"] = "Druid"  # ← Ajuste aqui
    bot.config["use_script_engine"] = True   # Usa scripts

    # ========================================
    # TESTE 1: HEALING SCRIPT
    # ========================================
    logger.info("\n" + "=" * 70)
    logger.info("TESTE 1: HEALING SCRIPT")
    logger.info("=" * 70)
    
    healing = HealingScript()
    healing.config["hp_threshold"] = 70        # Cura quando HP < 70%
    healing.config["mana_threshold"] = 25      # Precisa de 25% mana
    healing.config["spell_light"] = "exura"
    healing.config["spell_strong"] = "exura gran"
    healing.config["hp_light"] = 80            # Light heal se HP > 80%
    healing.config["hp_strong"] = 50           # Strong heal se HP 50-80%
    
    bot.script_engine.register(healing)
    bot.script_engine.enable_script("HealingBot")
    
    logger.info("✓ HealingBot configurado:")
    logger.info(f"  - Threshold: {healing.config['hp_threshold']}%")
    logger.info(f"  - Light heal: {healing.config['spell_light']} (>80% HP)")
    logger.info(f"  - Strong heal: {healing.config['spell_strong']} (50-80% HP)")

    # ========================================
    # TESTE 2: AIMBOT SCRIPT
    # ========================================
    logger.info("\n" + "=" * 70)
    logger.info("TESTE 2: AIMBOT SCRIPT")
    logger.info("=" * 70)
    
    aimbot = AimbotScript()
    aimbot.config["combat_mode"] = "lowest_hp"
    aimbot.config["max_distance"] = 7
    aimbot.config["attack_hotkey"] = "F1"
    aimbot.config["min_hp_to_attack"] = 40     # Não ataca se HP < 40%
    aimbot.config["target_blacklist"] = [
        "Training Assistant",
        "Rashid",
    ]
    
    bot.script_engine.register(aimbot)
    bot.script_engine.enable_script("AimBot")
    
    logger.info("✓ AimBot configurado:")
    logger.info(f"  - Modo: {aimbot.config['combat_mode']}")
    logger.info(f"  - Distância máx: {aimbot.config['max_distance']}")
    logger.info(f"  - Blacklist: {aimbot.config['target_blacklist']}")

    # ========================================
    # TESTE 3: EVENT SYSTEM
    # ========================================
    logger.info("\n" + "=" * 70)
    logger.info("TESTE 3: EVENT SYSTEM")
    logger.info("=" * 70)
    
    handlers = EventHandlers()
    
    # Subscreve eventos
    bot.event_manager.subscribe(EventType.PLAYER_HEALTH_LOW, handlers.on_health_low)
    bot.event_manager.subscribe(EventType.PLAYER_MANA_LOW, handlers.on_mana_low)
    bot.event_manager.subscribe(EventType.CREATURE_DETECTED, handlers.on_creature_detected)
    bot.event_manager.subscribe(EventType.LEVEL_UP, handlers.on_level_up)
    
    logger.info("✓ Event handlers registrados:")
    logger.info("  - PLAYER_HEALTH_LOW → on_health_low")
    logger.info("  - PLAYER_MANA_LOW → on_mana_low")
    logger.info("  - CREATURE_DETECTED → on_creature_detected")
    logger.info("  - LEVEL_UP → on_level_up")

    # ========================================
    # TESTE 4: CUSTOM EVENT HANDLER
    # ========================================
    logger.info("\n" + "=" * 70)
    logger.info("TESTE 4: CUSTOM EVENT HANDLER")
    logger.info("=" * 70)
    
    def my_custom_handler(**kwargs):
        """Handler customizado para testar."""
        creature_name = kwargs.get("creature_name", "Unknown")
        logger.info(f"🎯 CUSTOM EVENT: Nova criatura '{creature_name}' detectada!")
    
    bot.event_manager.subscribe(EventType.CREATURE_DETECTED, my_custom_handler)
    logger.info("✓ Custom handler registrado!")

    # ========================================
    # LISTA DE SCRIPTS
    # ========================================
    logger.info("\n" + "=" * 70)
    logger.info("SCRIPTS ATIVOS")
    logger.info("=" * 70)
    
    for script in bot.script_engine.list_scripts():
        status = "✓ ATIVO" if script["enabled"] else "✗ Inativo"
        logger.info(f"{status:12s} - {script['name']:15s} (prioridade: {script['priority']})")

    # ========================================
    # INICIA BOT
    # ========================================
    logger.info("\n" + "=" * 70)
    logger.info("INICIANDO BOT COM SCRIPT ENGINE")
    logger.info("=" * 70)
    logger.info("\n🎮 INSTRUÇÕES PARA TESTAR:")
    logger.info("  1. HealingBot: Deixe criaturas baterem em você até HP < 70%")
    logger.info("  2. AimBot: Aproxime-se de criaturas (vai atacar automaticamente)")
    logger.info("  3. Events: Observe os logs quando eventos acontecerem")
    logger.info("\nPressione Ctrl+C para parar.\n")
    
    bot.enabled = True  # Habilita o bot

    try:
        bot.run_loop(interval=0.1)
    except KeyboardInterrupt:
        logger.info("\n✓ Teste interrompido pelo usuário.")
    finally:
        bot.stop()
        logger.info("✓ Bot encerrado.")


if __name__ == "__main__":
    main()
