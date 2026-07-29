"""
AI de combate inteligente.
"""
from typing import List, Optional
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.position import Position
from .threat_analyzer import ThreatAnalyzer
from .skill_rotation import Skill, SkillRotation, DruidRotation, SorcererRotation, KnightRotation, PaladinRotation
from src.infrastructure.logging.logger import get_logger


class CombatAI:
    """AI de combate com análise de ameaças e skill rotation."""
    
    def __init__(self, player_vocation: str = "Druid"):
        self.threat_analyzer = ThreatAnalyzer()
        self.skill_rotation = self._create_rotation(player_vocation)
        self._log = get_logger("CombatAI")
        
        self.enabled = True
        self.auto_flee = True
        self.auto_use_skills = True
    
    def _create_rotation(self, vocation: str) -> SkillRotation:
        """Cria rotação baseada na vocação."""
        vocation_lower = vocation.lower()
        
        if "druid" in vocation_lower:
            return DruidRotation()
        elif "sorcerer" in vocation_lower or "sorc" in vocation_lower:
            return SorcererRotation()
        elif "knight" in vocation_lower:
            return KnightRotation()
        elif "paladin" in vocation_lower:
            return PaladinRotation()
        else:
            return SkillRotation()
    
    def analyze_situation(
        self,
        player: Player,
        creatures: List[Creature]
    ) -> dict:
        """
        Analisa situação de combate.
        
        Returns:
            Dicionário com análise completa
        """
        # Analisa ameaças
        should_flee = self.threat_analyzer.should_flee(player, creatures)
        highest_threat = self.threat_analyzer.get_highest_threat(creatures, player)
        
        # Próxima skill
        next_skill = self.skill_rotation.get_next_skill(player, highest_threat)
        
        # Direção de fuga
        safe_direction = None
        if should_flee:
            safe_direction = self.threat_analyzer.get_safe_direction(player, creatures)
        
        return {
            "should_flee": should_flee,
            "safe_direction": safe_direction,
            "highest_threat": highest_threat,
            "next_skill": next_skill,
            "total_creatures": len(creatures),
            "player_hp_pct": player.hp_percent(),
            "player_mana_pct": player.mana_percent(),
        }
    
    def decide_action(
        self,
        player: Player,
        creatures: List[Creature]
    ) -> str:
        """
        Decide ação baseado na situação.
        
        Returns:
            Ação: "flee", "use_skill", "attack", "idle"
        """
        if not self.enabled:
            return "idle"
        
        analysis = self.analyze_situation(player, creatures)
        
        # Prioridade 1: Fugir se necessário
        if self.auto_flee and analysis["should_flee"]:
            self._log.warning("🏃 AI decidiu FUGIR!")
            return "flee"
        
        # Prioridade 2: Usar skill se disponível
        if self.auto_use_skills and analysis["next_skill"]:
            skill = analysis["next_skill"]
            self._log.info(f"🔮 AI decidiu usar skill: {skill.name}")
            return "use_skill"
        
        # Prioridade 3: Atacar alvo de maior ameaça
        if analysis["highest_threat"]:
            return "attack"
        
        # Nada a fazer
        return "idle"
    
    def get_target(
        self,
        player: Player,
        creatures: List[Creature]
    ) -> Optional[Creature]:
        """Retorna melhor alvo baseado em análise de ameaças."""
        return self.threat_analyzer.get_highest_threat(creatures, player)

    def mark_skill_used(self, skill_name: str) -> None:
        """Marca skill como usada para iniciar cooldown."""
        for skill in self.skill_rotation.skills:
            if skill.name == skill_name:
                self.skill_rotation.mark_used(skill)
                return

    def get_next_skill(
        self,
        player: Player,
        target: Optional[Creature] = None
    ) -> Optional[Skill]:
        """Retorna próxima skill disponível."""
        return self.skill_rotation.get_next_skill(player, target)
