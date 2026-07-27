"""
Script de gerenciamento de buffs automáticos.
Inspiração: ElfBot/WindBot - manter buffs ativos durante caçadas.
"""
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from .base_script import BaseScript
from src.core.entities.player import Player


@dataclass
class Buff:
    """Representa um buff que pode ser mantido ativo."""
    name: str
    spell: str
    duration: float          # Duração em segundos
    cooldown: float = 0      # Cooldown após expirar antes de recastar
    mana_cost: int = 0       # Custo de mana mínimo para usar
    min_level: int = 0       # Level mínimo para usar
    vocations: list = field(default_factory=list)  # Vocações que podem usar (vazio = todas)
    last_cast: float = 0     # Timestamp do último cast


class BuffScript(BaseScript):
    """Script que mantém buffs ativos automaticamente."""
    
    # Definições de buffs por vocação (Tibia 8.60)
    BUFF_DEFINITIONS = {
        # Buffs universais
        "magic_shield": Buff(
            name="Magic Shield",
            spell="utamo vita",
            duration=180.0,        # 3 minutos
            cooldown=2.0,
            mana_cost=50,
            min_level=20,
        ),
        # Buffs físicos (Knights/Paladins)
        "haste": Buff(
            name="Haste",
            spell="utani hur",
            duration=20.0,         # 20 segundos
            cooldown=2.0,
            mana_cost=20,
            min_level=10,
            vocations=["Knight", "Elite Knight", "Paladin", "Royal Paladin"],
        ),
        "strong_haste": Buff(
            name="Strong Haste",
            spell="utani gran hur",
            duration=22.0,
            cooldown=2.0,
            mana_cost=100,
            min_level=40,
            vocations=["Knight", "Elite Knight", "Paladin", "Royal Paladin"],
        ),
        # Buffs mágicos (Mages)
        "utito_tempo": Buff(
            name="Utito Tempo",
            spell="utito tempo",
            duration=120.0,        # 2 minutos
            cooldown=2.0,
            mana_cost=220,
            min_level=60,
            vocations=["Sorcerer", "Master Sorcerer", "Druid", "Elder Druid"],
        ),
        # Strengthen (Knights)
        "strength_skill": Buff(
            name="Strength Skill",
            spell="exori infir vis",
            duration=180.0,
            cooldown=2.0,
            mana_cost=115,
            min_level=35,
            vocations=["Knight", "Elite Knight"],
        ),
        # MagicShield para mages
        "ultimate_magic_shield": Buff(
            name="Ultimate Magic Shield",
            spell="utamo vita",
            duration=180.0,
            cooldown=2.0,
            mana_cost=200,
            min_level=45,
            vocations=["Sorcerer", "Master Sorcerer", "Druid", "Elder Druid"],
        ),
        # Invisible (para fugas)
        "invisible": Buff(
            name="Invisible",
            spell="utana vid",
            duration=180.0,
            cooldown=2.0,
            mana_cost=440,
            min_level=35,
            vocations=["Sorcerer", "Master Sorcerer", "Druid", "Elder Druid"],
        ),
    }
    
    def __init__(self):
        super().__init__("BuffManager")
        self.priority = 90  # Alta prioridade, mas abaixo do healing
        self.config = {
            "enabled_buffs": ["magic_shield", "haste"],  # Buffs ativos por padrão
            "min_mana_pct": 30,                           # % mana mínima para manter buffs
            "min_hp_pct": 20,                             # % HP mínimo (não buffar se muito baixo)
            "check_interval": 1.0,                        # Intervalo entre verificações (segundos)
            "pre_cast_delay": 2.0,                        # Recastar X segundos antes de expirar
        }
        self._last_check = 0
        self._active_buffs: Dict[str, Buff] = {}

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        current_time = time.time()
        
        # Respeita intervalo de verificação
        if current_time - self._last_check < self.config["check_interval"]:
            return False
        
        self._last_check = current_time
        
        # Não buffar se HP muito baixo (prioriza cura)
        if player.hp_percent() < self.config["min_hp_pct"]:
            return False
        
        # Não buffar se mana muito baixa
        if player.mana_percent() < self.config["min_mana_pct"]:
            return False

        any_buff_cast = False
        
        # Verifica cada buff habilitado
        for buff_key in self.config["enabled_buffs"]:
            buff = self.BUFF_DEFINITIONS.get(buff_key)
            if not buff:
                continue
            
            # Verifica se o player pode usar este buff
            if not self._can_use_buff(buff, player):
                continue
            
            # Verifica se precisa recastar
            if self._needs_recast(buff, current_time):
                # Tenta castar
                if self._cast_buff(buff, bot_engine, current_time):
                    any_buff_cast = True
                    self._log.info(f"⚡ Buff ativado: {buff.name} ({buff.spell})")
                    # Pequeno delay entre buffs para evitar spam
                    time.sleep(0.3)
        
        return any_buff_cast

    def _can_use_buff(self, buff: Buff, player: Player) -> bool:
        """Verifica se o player pode usar este buff."""
        # Verifica level
        if buff.min_level > 0 and player.level < buff.min_level:
            return False
        
        # Verifica vocação
        if buff.vocations and player.vocation not in buff.vocations:
            # Tenta match parcial (ex: "Knight" em "Elite Knight")
            vocation_match = any(
                voc.lower() in player.vocation.lower() 
                for voc in buff.vocations
            )
            if not vocation_match:
                return False
        
        # Verifica mana
        if buff.mana_cost > 0 and player.stats.mana < buff.mana_cost:
            return False
        
        return True

    def _needs_recast(self, buff: Buff, current_time: float) -> bool:
        """Determina se o buff precisa ser recastado."""
        # Se nunca foi castado
        if buff.last_cast == 0:
            return True
        
        # Calcula tempo desde o último cast
        elapsed = current_time - buff.last_cast
        
        # Recastar se está perto de expirar (com margem de segurança)
        time_to_expire = buff.duration - elapsed
        if time_to_expire <= self.config["pre_cast_delay"]:
            return True
        
        # Respeita cooldown
        if elapsed < buff.cooldown:
            return False
        
        return False

    def _cast_buff(self, buff: Buff, bot_engine, current_time: float) -> bool:
        """Lança o buff."""
        try:
            bot_engine._injector.cast_spell(buff.spell)
            buff.last_cast = current_time
            self._active_buffs[buff.name] = buff
            return True
        except Exception as e:
            self._log.error(f"Erro ao castar buff {buff.name}: {e}")
            return False

    def get_active_buffs(self) -> Dict[str, Buff]:
        """Retorna buffs atualmente ativos."""
        current_time = time.time()
        active = {}
        for name, buff in self._active_buffs.items():
            elapsed = current_time - buff.last_cast
            if elapsed < buff.duration:
                active[name] = buff
        return active

    def get_buff_time_remaining(self, buff_name: str) -> Optional[float]:
        """Retorna tempo restante de um buff específico."""
        buff = self._active_buffs.get(buff_name)
        if not buff:
            return None
        elapsed = time.time() - buff.last_cast
        remaining = buff.duration - elapsed
        return max(0, remaining)

    def force_recast(self, buff_name: str) -> bool:
        """Força recast de um buff específico na próxima execução."""
        buff = self.BUFF_DEFINITIONS.get(buff_name)
        if buff:
            buff.last_cast = 0
            return True
        return False

    def enable_buff(self, buff_name: str) -> bool:
        """Habilita um buff para ser mantido ativo."""
        if buff_name in self.BUFF_DEFINITIONS:
            if buff_name not in self.config["enabled_buffs"]:
                self.config["enabled_buffs"].append(buff_name)
            return True
        return False

    def disable_buff(self, buff_name: str) -> bool:
        """Desabilita um buff."""
        if buff_name in self.config["enabled_buffs"]:
            self.config["enabled_buffs"].remove(buff_name)
            return True
        return False

    def get_available_buffs_for_vocation(self, vocation: str) -> list:
        """Retorna lista de buffs disponíveis para a vocação do player."""
        available = []
        for key, buff in self.BUFF_DEFINITIONS.items():
            if not buff.vocations:
                available.append(key)
            elif any(voc.lower() in vocation.lower() for voc in buff.vocations):
                available.append(key)
        return available