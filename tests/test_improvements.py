"""
Teste das melhorias implementadas - valida os novos scripts sem precisar do Tibia.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.application.scripts.healing_script import HealingScript
from src.application.scripts.buff_script import BuffScript
from src.application.scripts.aimbot_script import AimbotScript
from src.application.scripts.cavebot_script import CavebotScript
from src.application.scripts.looter_script import LooterScript
from src.application.stats_tracker import StatsTracker
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats
from src.infrastructure.logging.logger import setup_logging

import os
os.makedirs("logs", exist_ok=True)
setup_logging(level="INFO", log_file="logs/test_improvements.log")

from src.infrastructure.logging.logger import get_logger
logger = get_logger("TestImprovements")


def create_test_player():
    """Cria player de teste."""
    return Player(
        id=1001,
        name="TestPlayer",
        position=Position(100, 100, 7),
        stats=Stats(health=500, max_health=1000, mana=200, max_mana=500),
        level=50,
        experience=100000,
        magic_level=20,
        soul=100,
        stamina=1440,
        capacity=500,
        vocation="Druid",
    )


def create_test_creatures():
    """Cria criaturas de teste."""
    return [
        Creature(
            id=2001,
            name="Dragon",
            position=Position(102, 101, 7),
            stats=Stats(health=80, max_health=100, mana=0, max_mana=0),
            visible=True,
            walking=False,
        ),
        Creature(
            id=2002,
            name="Rotworm",
            position=Position(105, 105, 7),
            stats=Stats(health=30, max_health=100, mana=0, max_mana=0),
            visible=True,
            walking=False,
        ),
    ]


class MockInjector:
    """Injector mock para testes."""
    def __init__(self):
        self.spells_cast = []
        self.hotkeys_sent = []
        self.keys_sent = []
    
    def cast_spell(self, spell):
        self.spells_cast.append(spell)
        logger.info(f"[MOCK] Cast spell: {spell}")
    
    def send_hotkey(self, key):
        self.hotkeys_sent.append(key)
        logger.info(f"[MOCK] Send hotkey: {key}")
    
    def send_key_background(self, vk_code):
        self.keys_sent.append(vk_code)
        logger.info(f"[MOCK] Send key: {vk_code}")


class MockBotEngine:
    """Bot engine mock para testes."""
    def __init__(self):
        self._injector = MockInjector()
        self.config = {"player_vocation": "Druid"}


def test_healing_script():
    """Testa HealingScript melhorado."""
    logger.info("=" * 60)
    logger.info("🧪 TESTE 1: HealingScript com DPS-based healing")
    logger.info("=" * 60)
    
    healing = HealingScript()
    healing.enabled = True
    
    # Player com HP baixo
    player = create_test_player()
    player.stats.health = 400  # 40% HP
    
    bot_engine = MockBotEngine()
    context = {"player": player, "bot_engine": bot_engine}
    
    # Primeira execução - deve curar
    result = healing.execute(context)
    logger.info(f"Resultado (HP 40%): {result}")
    logger.info(f"Spells cast: {bot_engine._injector.spells_cast}")
    
    # Testar com HP crítico
    player.stats.health = 100  # 10% HP
    healing.config["last_heal_time"] = 0  # Reset cooldown
    result = healing.execute(context)
    logger.info(f"Resultado (HP 10%): {result}")
    logger.info(f"Spells cast: {bot_engine._injector.spells_cast}")
    
    # Testar configurações
    assert healing.config["enable_dps_healing"] == True
    assert healing.config["spell_mana_drain"] == "exura sio"
    assert healing.config["spell_sacrifice"] == "utana vid"
    logger.info("✓ HealingScript OK")
    logger.info("")


def test_buff_script():
    """Testa BuffScript."""
    logger.info("=" * 60)
    logger.info("🧪 TESTE 2: BuffScript - gerenciamento de buffs")
    logger.info("=" * 60)
    
    buff_script = BuffScript()
    buff_script.enabled = True
    
    # Player com level suficiente
    player = create_test_player()
    player.stats.mana = 300  # Mana suficiente
    
    bot_engine = MockBotEngine()
    context = {"player": player, "bot_engine": bot_engine}
    
    # Executar - deve tentar manter magic shield
    result = buff_script.execute(context)
    logger.info(f"Resultado: {result}")
    logger.info(f"Spells cast: {bot_engine._injector.spells_cast}")
    
    # Verificar buffs disponíveis para Druid
    available = buff_script.get_available_buffs_for_vocation("Druid")
    logger.info(f"Buffs disponíveis para Druid: {available}")
    
    # Testar ativação de buff
    assert buff_script.enable_buff("magic_shield") == True
    assert buff_script.disable_buff("nonexistent") == False
    logger.info("✓ BuffScript OK")
    logger.info("")


def test_aimbot_script():
    """Testa AimbotScript com targeting avançado."""
    logger.info("=" * 60)
    logger.info("🧪 TESTE 3: AimbotScript - targeting por XP")
    logger.info("=" * 60)
    
    aimbot = AimbotScript()
    aimbot.enabled = True
    aimbot.config["targeting_mode"] = "highest_xp"
    
    player = create_test_player()
    creatures = create_test_creatures()
    bot_engine = MockBotEngine()
    
    context = {"player": player, "creatures": creatures, "bot_engine": bot_engine}
    
    # Executar - deve selecionar Dragon (mais XP)
    result = aimbot.execute(context)
    logger.info(f"Resultado: {result}")
    logger.info(f"Hotkeys sent: {bot_engine._injector.hotkeys_sent}")
    logger.info(f"Spells cast (combo): {bot_engine._injector.spells_cast}")
    
    # Verificar target selecionado
    target = aimbot.get_current_target()
    if target:
        logger.info(f"Target selecionado: {target.name} (HP: {target.stats.health}%)")
    
    # Testar targeting modes
    aimbot.config["targeting_mode"] = "lowest_hp"
    aimbot.clear_target()
    aimbot.config["cooldown"] = 0
    result = aimbot.execute(context)
    target = aimbot.get_current_target()
    if target:
        logger.info(f"Modo lowest_hp - Target: {target.name} (HP: {target.stats.health}%)")
    
    logger.info("✓ AimbotScript OK")
    logger.info("")


def test_cavebot_script():
    """Testa CavebotScript com anti-stuck."""
    logger.info("=" * 60)
    logger.info("🧪 TESTE 4: CavebotScript - anti-stuck e follow")
    logger.info("=" * 60)
    
    cavebot = CavebotScript()
    cavebot.enabled = True
    cavebot.add_waypoint(Waypoint(Position(105, 105, 7), action="walk"))
    
    player = create_test_player()
    bot_engine = MockBotEngine()
    context = {"player": player, "creatures": [], "bot_engine": bot_engine}
    
    # Executar
    result = cavebot.execute(context)
    logger.info(f"Resultado: {result}")
    logger.info(f"Keys sent: {bot_engine._injector.keys_sent}")
    
    # Testar modo follow
    cavebot.start_follow("TestFriend", distance=2)
    assert cavebot.config["enable_follow"] == True
    assert cavebot.config["follow_target_name"] == "TestFriend"
    
    cavebot.stop_follow()
    assert cavebot.config["enable_follow"] == False
    
    # Status
    status = cavebot.get_status()
    logger.info(f"Status: {status}")
    
    logger.info("✓ CavebotScript OK")
    logger.info("")


def test_looter_script():
    """Testa LooterScript."""
    logger.info("=" * 60)
    logger.info("🧪 TESTE 5: LooterScript - tracking de kills")
    logger.info("=" * 60)
    
    looter = LooterScript()
    
    # Registrar kill
    creature = create_test_creatures()[0]
    looter.register_kill(creature)
    
    player = create_test_player()
    bot_engine = MockBotEngine()
    context = {"player": player, "creatures": [], "bot_engine": bot_engine}
    
    # Executar
    result = looter.execute(context)
    logger.info(f"Resultado: {result}")
    
    # Stats
    stats = looter.get_loot_stats()
    logger.info(f"Loot stats: {stats}")
    
    # Testar adicionar/remover items
    looter.add_item_to_loot(9999, "Test Item")
    assert looter.remove_item_from_loot(9999) == True
    
    logger.info("✓ LooterScript OK")
    logger.info("")


def test_stats_tracker():
    """Testa StatsTracker para HUD."""
    logger.info("=" * 60)
    logger.info("🧪 TESTE 6: StatsTracker - HUD e estatísticas")
    logger.info("=" * 60)
    
    tracker = StatsTracker()
    player = create_test_player()
    creatures = create_test_creatures()
    
    # Iniciar sessão
    tracker.start_session(player)
    
    # Simular updates
    tracker.update(player, creatures)
    
    # Registrar kills
    for _ in range(5):
        tracker.register_kill(creatures[0])  # Dragon kills
    for _ in range(3):
        tracker.register_kill(creatures[1])  # Rotworm kills
    
    # Registrar heals
    for _ in range(10):
        tracker.register_heal("exura gran")
    
    # Registrar loot
    tracker.register_loot(3031, "Gold Coin", 50)
    tracker.register_loot(3035, "Platinum Coin", 100)
    
    # Obter HUD text
    hud_text = tracker.get_hud_text()
    logger.info("\n" + hud_text)
    
    # Obter stats
    stats = tracker.get_stats_summary()
    logger.info(f"Stats: {stats}")
    
    # Verificar cálculos
    assert stats["total_kills"] == 8
    assert stats["total_heals"] == 10
    assert stats["total_loot"] == 2
    assert stats["total_gold"] == 150
    assert "Dragon" in stats["creatures_killed"]
    assert stats["creatures_killed"]["Dragon"] == 5
    
    logger.info("✓ StatsTracker OK")
    logger.info("")
    
    tracker.stop_session()


def main():
    logger.info("=" * 60)
    logger.info("🎮 TESTE DAS MELHORIAS DO TIBIA BOT 8.60")
    logger.info("=" * 60)
    logger.info("")
    
    try:
        test_healing_script()
        test_buff_script()
        test_aimbot_script()
        test_cavebot_script()
        test_looter_script()
        test_stats_tracker()
        
        logger.info("=" * 60)
        logger.info("✅ TODOS OS TESTES PASSARAM!")
        logger.info("=" * 60)
        
        logger.info("\n📝 Resumo das melhorias implementadas:")
        logger.info("  1. HealingScript: DPS-based healing, exura sio, utana vid, overheal protection")
        logger.info("  2. BuffScript: Gerenciamento automático de buffs (magic shield, haste, etc.)")
        logger.info("  3. AimbotScript: Targeting por XP/HP, combo attacks, anti-lure")
        logger.info("  4. CavebotScript: Anti-stuck, follow system, pause em combate")
        logger.info("  5. LooterScript: Tracking de kills, loot filter, loot por valor")
        logger.info("  6. StatsTracker: HUD com XP/h, gold/h, kills/h, tempo de sessão")
        logger.info("  7. addresses_860.py: Container, Hotkey, PlayerSlots, PlayerExtra, VIP")
        
    except Exception as e:
        logger.error(f"❌ Teste falhou: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()