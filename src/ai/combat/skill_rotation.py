"""
Sistema de rotação de skills/spells.
"""
from typing import List, Dict, Optional
from dataclasses import dataclass
from src.core.entities.player import Player
from src.core.entities.creature import Creature
import time


@dataclass
class Skill:
    """Representa uma skill/spell."""
    name: str
    mana_cost: int
    cooldown: float  # segundos
    min_hp_target: int = 0  # HP mínimo do alvo para usar
    max_hp_target: int = 100  # HP máximo do alvo para usar
    min_mana_player: int = 0  # Mana mínima do player
    words: str = ""  # Palavras mágicas
    hotkey: str = ""  # Hotkey alternativa


class SkillRotation:
    """Gerencia rotação de skills em combate."""
    
    def __init__(self):
        self.skills: List[Skill] = []
        self.last_used: Dict[str, float] = {}
        self.enabled = True
    
    def add_skill(self, skill: Skill) -> None:
        """Adiciona skill à rotação."""
        self.skills.append(skill)
    
    def can_use_skill(
        self,
        skill: Skill,
        player: Player,
        target: Optional[Creature] = None
    ) -> bool:
        """Verifica se pode usar skill."""
        # Verifica cooldown
        last_use = self.last_used.get(skill.name, 0)
        if time.time() - last_use < skill.cooldown:
            return False
        
        # Verifica mana do player
        if player.stats.mana < skill.mana_cost:
            return False
        
        if player.mana_percent() < skill.min_mana_player:
            return False
        
        # Se tem alvo, verifica HP do alvo
        if target:
            target_hp = target.stats.health
            if not (skill.min_hp_target <= target_hp <= skill.max_hp_target):
                return False
        
        return True
    
    def get_next_skill(
        self,
        player: Player,
        target: Optional[Creature] = None
    ) -> Optional[Skill]:
        """
        Retorna próxima skill disponível na rotação.
        
        Args:
            player: Player
            target: Alvo opcional
            
        Returns:
            Skill ou None se nenhuma disponível
        """
        if not self.enabled or not self.skills:
            return None
        
        for skill in self.skills:
            if self.can_use_skill(skill, player, target):
                return skill
        
        return None
    
    def mark_used(self, skill: Skill) -> None:
        """Marca skill como usada (inicia cooldown)."""
        self.last_used[skill.name] = time.time()
    
    def reset_cooldowns(self) -> None:
        """Reseta todos os cooldowns."""
        self.last_used.clear()


class DruidRotation(SkillRotation):
    """Rotação específica para Druid."""
    
    def __init__(self):
        super().__init__()
        
        # Skills ofensivas
        self.add_skill(Skill(
            name="Strike",
            mana_cost=20,
            cooldown=2.0,
            words="exori flam",
            min_hp_target=50,  # Usa em alvos com HP > 50%
        ))
        
        self.add_skill(Skill(
            name="Terra Wave",
            mana_cost=170,
            cooldown=4.0,
            words="exevo tera hur",
            min_mana_player=40,  # Só usa se tiver > 40% mana
        ))
        
        # Skills de suporte
        self.add_skill(Skill(
            name="Magic Shield",
            mana_cost=50,
            cooldown=14.0,
            words="utamo vita",
            min_mana_player=50,
        ))


class SorcererRotation(SkillRotation):
    """Rotação específica para Sorcerer."""
    
    def __init__(self):
        super().__init__()
        
        self.add_skill(Skill(
            name="Energy Strike",
            mana_cost=20,
            cooldown=2.0,
            words="exori vis",
            min_hp_target=50,
        ))
        
        self.add_skill(Skill(
            name="Energy Wave",
            mana_cost=170,
            cooldown=4.0,
            words="exevo vis hur",
            min_mana_player=40,
        ))
        
        self.add_skill(Skill(
            name="Magic Shield",
            mana_cost=50,
            cooldown=14.0,
            words="utamo vita",
            min_mana_player=50,
        ))


class KnightRotation(SkillRotation):
    """Rotação específica para Knight."""
    
    def __init__(self):
        super().__init__()
        
        self.add_skill(Skill(
            name="Berserk",
            mana_cost=115,
            cooldown=4.0,
            words="exori",
            min_mana_player=30,
        ))
        
        self.add_skill(Skill(
            name="Groundshaker",
            mana_cost=210,
            cooldown=8.0,
            words="exori mas",
            min_mana_player=40,
        ))


class PaladinRotation(SkillRotation):
    """Rotação específica para Paladin."""
    
    def __init__(self):
        super().__init__()
        
        self.add_skill(Skill(
            name="Divine Missile",
            mana_cost=20,
            cooldown=2.0,
            words="exori san",
            min_hp_target=40,
        ))
        
        self.add_skill(Skill(
            name="Divine Caldera",
            mana_cost=160,
            cooldown=4.0,
            words="exevo mas san",
            min_mana_player=35,
        ))
