"""
Análise de ameaças em combate.
"""
from typing import List, Dict
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position


class ThreatLevel:
    """Níveis de ameaça."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ThreatAnalyzer:
    """Analisa ameaças no combate."""
    
    def __init__(self):
        # Configuração de ameaças por criatura
        self.creature_threat_levels = {
            "Dragon": ThreatLevel.HIGH,
            "Dragon Lord": ThreatLevel.CRITICAL,
            "Demon": ThreatLevel.CRITICAL,
            "Rotworm": ThreatLevel.LOW,
            "Rat": ThreatLevel.LOW,
        }
    
    def analyze_creature(
        self,
        creature: Creature,
        player: Player
    ) -> int:
        """
        Analisa ameaça de uma criatura.
        
        Returns:
            Valor de ameaça (0-100)
        """
        threat = 0
        
        # Base threat por nome
        base_threat = self.creature_threat_levels.get(
            creature.name,
            ThreatLevel.MEDIUM
        ) * 15
        threat += base_threat
        
        # HP da criatura (quanto maior, mais ameaça)
        threat += (creature.stats.health / 100) * 10
        
        # Distância (quanto mais perto, mais ameaça)
        distance = player.position.distance_chebyshev(creature.position)
        if distance <= 1:
            threat += 30
        elif distance <= 3:
            threat += 20
        elif distance <= 5:
            threat += 10
        
        # Se está visível e andando (mais agressivo)
        if creature.visible and creature.walking:
            threat += 5
        
        return min(int(threat), 100)
    
    def get_highest_threat(
        self,
        creatures: List[Creature],
        player: Player
    ) -> Creature | None:
        """Retorna criatura com maior ameaça."""
        if not creatures:
            return None
        
        threats = [
            (creature, self.analyze_creature(creature, player))
            for creature in creatures
        ]
        
        # Ordena por ameaça (maior primeiro)
        threats.sort(key=lambda x: x[1], reverse=True)
        
        return threats[0][0] if threats else None
    
    def should_flee(
        self,
        player: Player,
        creatures: List[Creature]
    ) -> bool:
        """
        Decide se deve fugir.
        
        Returns:
            True se deve fugir
        """
        # Foge se HP muito baixo
        if player.hp_percent() < 20:
            return True
        
        # Conta criaturas próximas perigosas
        dangerous_nearby = 0
        for creature in creatures:
            distance = player.position.distance_chebyshev(creature.position)
            threat = self.analyze_creature(creature, player)
            
            if distance <= 3 and threat >= 50:
                dangerous_nearby += 1
        
        # Foge se muitas criaturas perigosas próximas
        if dangerous_nearby >= 3:
            return True
        
        return False
    
    def get_safe_direction(
        self,
        player: Player,
        creatures: List[Creature]
    ) -> Position | None:
        """
        Retorna direção mais segura para fugir.
        
        Returns:
            Posição sugerida ou None
        """
        # Calcula centro de massa das criaturas
        if not creatures:
            return None
        
        avg_x = sum(c.position.x for c in creatures) / len(creatures)
        avg_y = sum(c.position.y for c in creatures) / len(creatures)
        
        # Foge na direção oposta
        dx = player.position.x - avg_x
        dy = player.position.y - avg_y
        
        # Normaliza e multiplica por 3 (foge 3 SQMs)
        magnitude = (dx**2 + dy**2)**0.5
        if magnitude == 0:
            return None
        
        safe_x = int(player.position.x + (dx / magnitude) * 3)
        safe_y = int(player.position.y + (dy / magnitude) * 3)
        
        return Position(safe_x, safe_y, player.position.z)
