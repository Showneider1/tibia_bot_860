"""
Teste completo da FASE 3 - AI & Pathfinding.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ai.pathfinding.pathfinder import Pathfinder
from src.ai.pathfinding.astar import AStar
from src.ai.combat.combat_ai import CombatAI
from src.ai.combat.threat_analyzer import ThreatAnalyzer
from src.ai.combat.skill_rotation import DruidRotation
from src.ai.behavior.behavior_tree import BehaviorTree, NodeStatus
from src.ai.behavior.nodes import Selector, Sequence, Action, Condition
from src.ai.decision.decision_maker import DecisionMaker, Decision
from src.ai.decision.priorities import Priority
from src.core.value_objects.position import Position
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.stats import Stats
from src.infrastructure.logging.logger import get_logger


def test_pathfinding():
    """Teste de pathfinding."""
    logger = get_logger("TestPathfinding")
    logger.info("=" * 70)
    logger.info("🧪 TESTE 1: PATHFINDING (A*)")
    logger.info("=" * 70)
    
    pathfinder = Pathfinder()
    
    start = Position(100, 100, 7)
    goal = Position(110, 110, 7)
    
    logger.info(f"Início: {start}")
    logger.info(f"Objetivo: {goal}")
    
    path = pathfinder.find_path(start, goal, use_cache=False)
    
    if path:
        logger.info(f"✓ Caminho encontrado com {len(path)} passos!")
        logger.info(f"  Primeiro passo: {path[1] if len(path) > 1 else 'N/A'}")
        logger.info(f"  Último passo: {path[-1]}")
    else:
        logger.warning("✗ Nenhum caminho encontrado")
    
    logger.info("")


def test_combat_ai():
    """Teste de Combat AI."""
    logger = get_logger("TestCombatAI")
    logger.info("=" * 70)
    logger.info("🧪 TESTE 2: COMBAT AI")
    logger.info("=" * 70)
    
    # Cria player e criaturas
    player = Player(
        id=1,
        name="Test Player",
        position=Position(100, 100, 7),
        stats=Stats(150, 200, 80, 100),
        level=50,
        vocation="Druid"
    )
    
    creatures = [
        Creature(
            id=2,
            name="Dragon",
            position=Position(102, 101, 7),
            stats=Stats(80, 100, 0, 0),
            visible=True
        ),
        Creature(
            id=3,
            name="Rotworm",
            position=Position(105, 105, 7),
            stats=Stats(90, 100, 0, 0),
            visible=True
        ),
    ]
    
    combat_ai = CombatAI("Druid")
    
    logger.info(f"Player: {player.name} | HP: {player.hp_percent():.1f}%")
    logger.info(f"Criaturas: {len(creatures)}")
    
    # Analisa situação
    analysis = combat_ai.analyze_situation(player, creatures)
    
    logger.info(f"\n📊 Análise:")
    logger.info(f"  - Deve fugir: {analysis['should_flee']}")
    logger.info(f"  - Maior ameaça: {analysis['highest_threat'].name if analysis['highest_threat'] else 'Nenhuma'}")
    logger.info(f"  - Próxima skill: {analysis['next_skill'].name if analysis['next_skill'] else 'Nenhuma'}")
    
    # Decide ação
    action = combat_ai.decide_action(player, creatures)
    logger.info(f"\n🎯 Decisão: {action}")
    logger.info("")


def test_behavior_tree():
    """Teste de Behavior Tree."""
    logger = get_logger("TestBehaviorTree")
    logger.info("=" * 70)
    logger.info("🧪 TESTE 3: BEHAVIOR TREE")
    logger.info("=" * 70)
    
    # Define ações
    def check_hp_low(ctx):
        hp = ctx.get("hp_percent", 100)
        return hp < 50
    
    def heal_action(ctx):
        logger.info("  → Executando: HEAL")
        return True
    
    def check_enemy_nearby(ctx):
        enemies = ctx.get("enemies", 0)
        return enemies > 0
    
    def attack_action(ctx):
        logger.info("  → Executando: ATTACK")
        return True
    
    def idle_action(ctx):
        logger.info("  → Executando: IDLE")
        return True
    
    # Constrói árvore
    tree = BehaviorTree(
        Selector("Root", [
            Sequence("HealSequence", [
                Condition("CheckHPLow", check_hp_low),
                Action("Heal", heal_action)
            ]),
            Sequence("AttackSequence", [
                Condition("CheckEnemyNearby", check_enemy_nearby),
                Action("Attack", attack_action)
            ]),
            Action("Idle", idle_action)
        ])
    )
    
    # Teste 1: HP baixo
    logger.info("\nCenário 1: HP baixo (30%)")
    context = {"hp_percent": 30, "enemies": 0}
    status = tree.tick(context)
    logger.info(f"Status: {status.value}")
    
    # Teste 2: Inimigo próximo
    logger.info("\nCenário 2: Inimigo próximo")
    context = {"hp_percent": 80, "enemies": 1}
    status = tree.tick(context)
    logger.info(f"Status: {status.value}")
    
    # Teste 3: Idle
    logger.info("\nCenário 3: Nada para fazer")
    context = {"hp_percent": 100, "enemies": 0}
    status = tree.tick(context)
    logger.info(f"Status: {status.value}")
    logger.info("")


def test_decision_maker():
    """Teste de Decision Maker."""
    logger = get_logger("TestDecisionMaker")
    logger.info("=" * 70)
    logger.info("🧪 TESTE 4: DECISION MAKER")
    logger.info("=" * 70)
    
    dm = DecisionMaker()
    
    # Define decisões
    dm.add_decision(Decision(
        name="EMERGENCY_HEAL",
        priority=Priority.EMERGENCY_HEAL,
        condition=lambda ctx: ctx.get("hp_percent", 100) < 20,
        action=lambda ctx: logger.info("  → Ação: Curando emergencialmente!")
    ))
    
    dm.add_decision(Decision(
        name="FLEE",
        priority=Priority.FLEE,
        condition=lambda ctx: ctx.get("hp_percent", 100) < 30 and ctx.get("enemies", 0) > 2,
        action=lambda ctx: logger.info("  → Ação: Fugindo!")
    ))
    
    dm.add_decision(Decision(
        name="ATTACK",
        priority=Priority.USE_BASIC_ATTACK,
        condition=lambda ctx: ctx.get("enemies", 0) > 0,
        action=lambda ctx: logger.info("  → Ação: Atacando!")
    ))
    
    dm.add_decision(Decision(
        name="IDLE",
        priority=Priority.IDLE,
        condition=lambda ctx: True,
        action=lambda ctx: logger.info("  → Ação: Ocioso...")
    ))
    
    # Teste cenários
    logger.info("\nCenário 1: HP crítico")
    dm.decide({"hp_percent": 15, "enemies": 1})
    
    logger.info("\nCenário 2: HP baixo com muitos inimigos")
    dm.decide({"hp_percent": 25, "enemies": 3})
    
    logger.info("\nCenário 3: HP ok, inimigo próximo")
    dm.decide({"hp_percent": 80, "enemies": 1})
    
    logger.info("\nCenário 4: Nada acontecendo")
    dm.decide({"hp_percent": 100, "enemies": 0})
    logger.info("")


def main():
    logger = get_logger("Main")
    logger.info("=" * 70)
    logger.info("🎮 TIBIA BOT 8.60 - FASE 3 - AI & PATHFINDING")
    logger.info("=" * 70)
    logger.info("")
    
    test_pathfinding()
    test_combat_ai()
    test_behavior_tree()
    test_decision_maker()
    
    logger.info("=" * 70)
    logger.info("✅ TODOS OS TESTES DA FASE 3 CONCLUÍDOS!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
