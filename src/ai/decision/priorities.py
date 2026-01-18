"""
Sistema de prioridades pré-definidas.
"""


class Priority:
    """Níveis de prioridade padrão."""
    
    # Sobrevivência
    CRITICAL_HEALTH = 1000
    FLEE = 900
    EMERGENCY_HEAL = 800
    
    # Combate
    USE_ULTIMATE = 700
    USE_STRONG_ATTACK = 600
    USE_BASIC_ATTACK = 500
    TARGET_ENEMY = 400
    
    # Suporte
    HEAL = 300
    USE_BUFF = 200
    USE_MANA_POTION = 150
    
    # Navegação
    FOLLOW_PATH = 100
    EXPLORE = 50
    
    # Idle
    IDLE = 0
