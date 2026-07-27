import time
from typing import Dict, Any, Optional
from .base_script import BaseScript
from src.core.entities.player import Player


class HealingScript(BaseScript):
    """Script de auto-healing avançado com múltiplas estratégias."""
    
    def __init__(self):
        super().__init__("HealingBot")
        self.priority = 100  # Máxima prioridade
        self.config = {
            # Healing baseado em porcentagem de HP (método tradicional)
            "hp_threshold": 50,      # % de HP para curar
            "mana_threshold": 20,    # % mana mínima para curar
            
            # Healing baseado em dano recebido (método avançado)
            "enable_dps_healing": True,  # Ativar healing baseado em DPS
            "dps_threshold": 80,         # Curar se DPS > este valor (HP por segundo)
            "dps_window": 2.0,           # Janela de tempo para calcular DPS (segundos)
            
            # Spells disponíveis
            "spell_light": "exura",              # Cura leve
            "spell_strong": "exura gran",        # Cura forte
            "spell_ultimate": "exura vita",      # Cura máxima
            "spell_mana_drain": "exura sio",     # Cura que mana (exura sio)
            "spell_sacrifice": "utana vid",      # Converte mana para HP (alta level)
            
            # Configurações de cada spell
            "hp_light": 85,          # Usa light heal acima de 85% HP
            "hp_strong": 50,         # Usa strong heal entre 50-85% HP
            "hp_ultimate": 25,       # Usa ultimate heal abaixo de 25% HP
            "hp_mana_drain": 40,     # Usa mana drain heal entre 40-70% HP quando mana boa
            "mana_min_for_sd": 25,   # # mana mínima para considerar mana drain heal
            
            # Sacrifice (utana vid) - apenas para vocações que têm
            "enable_sacrifice": True,
            "sacrifice_hp_threshold": 15,  # HP% abaixo do qual usar sacrifice
            "sacrifice_mana_threshold": 40, # Mínimo de mana para usar sacrifice
            
            # Proteção contra overheal (desperdício de cura)
            "enable_overheat_protection": True,
            "overheat_threshold": 0.9,  # Não curar se o overheal for > 90% do heal
            
            # Cooldowns e timing
            "cooldown": 0.8,          # Cooldown entre heals (segundos)
            # Internal tracking (do not modify manually)
            "last_heal_time": 0,      
            "_last_hp": 0,            
            "_last_dps_check": 0,     
        }
        self._last_hp = 0
        self._last_dps_check = 0

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        current_time = time.time()
        
        # Atualizar tracking de HP para cálculo de DPS
        self._update_dps_tracking(player, current_time)
        
        # Verificar cooldown
        if current_time - self.config["last_heal_time"] < self.config["cooldown"]:
            return False

        # Verificar se precisa curar baseado em múltiplas condições
        should_heal, heal_type, reason = self._should_heal(player)
        
        if not should_heal:
            return False

        # Executar o heal
        success = self._execute_heal(player, bot_engine, heal_type)
        
        if success:
            self.config["last_heal_time"] = current_time
            self._log.info(f"🩹 Healing com '{heal_type}' ({reason}) - HP: {player.hp_percent():.1f}%")
            return True
            
        return False

    def _update_dps_tracking(self, player: Player, current_time: float) -> None:
        """Atualiza o tracking de HP para cálculo de dano por segundo."""
        if self._last_hp > 0 and self._last_dps_check > 0:
            time_diff = current_time - self._last_dps_check
            if time_diff > 0:
                # Calcule HP perdido (dano recebido) - note que cura aumenta HP, então
                # só consideramos perda de HP como dano
                hp_lost = max(0, self._last_hp - player.stats.health)
                if hp_lost > 0:
                    # Armazenar o DPS para uso em should_heal
                    self._current_dps = hp_lost / time_diff
                else:
                    self._current_dps = 0
            else:
                self._current_dps = 0
        else:
            self._current_dps = 0
            
        self._last_hp = player.stats.health
        self._last_dps_check = current_time

    def _should_heal(self, player: Player) -> tuple[bool, Optional[str], str]:
        """
        Determina se deve curar e qual tipo de heal usar.
        Returns: (should_heal, heal_type, reason)
        """
        hp_pct = player.hp_percent()
        mana_pct = player.mana_percent()
        
        # 1. Verificar se está morto ou com HP máximo
        if hp_pct >= 100:
            return False, None, "HP cheio"
            
        # 2. Verificar mana mínima
        if mana_pct < self.config["mana_threshold"]:
            return False, None, f"Mana baixa ({mana_pct:.1f}%)"
        
        # 3. Healing baseado em DPS (se ativado)
        if self.config["enable_dps_healing"] and hasattr(self, '_current_dps'):
            dps = getattr(self, '_current_dps', 0)
            if dps > self.config["dps_threshold"]:
                # DPS alto - usar heal mais forte baseado na urgência
                heal_type = self._select_heal_by_urgency(hp_pct, mana_pct, dps)
                if heal_type:
                    return True, heal_type, f"DPS alto ({dps:.1f} HP/s)"
        
        # 4. Healing tradicional baseado em porcentagem de HP
        heal_type = self._select_heal_by_hp_percentage(hp_pct, mana_pct)
        if heal_type:
            return True, heal_type, f"HP baixo ({hp_pct:.1f}%)"
            
        # 5. Verificar se deve usar sacrifice (utana vid) como último recurso
        if (self.config["enable_sacrifice"] and 
            hp_pct < self.config["sacrifice_hp_threshold"] and
            mana_pct > self.config["sacrifice_mana_threshold"]):
            return True, self.config["spell_sacrifice"], "Emergência - Sacrifice"
            
        return False, None, "Não precisa de cura"

    def _select_heal_by_urgency(self, hp_pct: float, mana_pct: float, dps: float) -> Optional[str]:
        """Seleciona heal baseado na urgência (DPS + HP%)."""
        # Se DPS muito alto e HP crítico, usar ultimate ou sacrifice
        if dps > 200 and hp_pct < 20:
            if mana_pct > 20 and self._can_cast(self.config["spell_ultimate"]):
                return self.config["spell_ultimate"]
            elif self.config["enable_sacrifice"] and mana_pct > self.config["sacrifice_mana_threshold"]:
                return self.config["spell_sacrifice"]
                
        # DPS alto, HP médio-baixo
        if dps > 100 and hp_pct < 40:
            if mana_pct > 25 and self._can_cast(self.config["spell_strong"]):
                return self.config["spell_strong"]
            elif self._can_cast(self.config["spell_light"]):
                return self.config["spell_light"]
                
        # DPS moderado
        if dps > 50 and hp_pct < 60:
            if mana_pct > 30 and self._can_cast(self.config["spell_mana_drain"]):
                return self.config["spell_mana_drain"]
            elif self._can_cast(self.config["spell_strong"]):
                return self.config["spell_strong"]
                
        return None

    def _select_heal_by_hp_percentage(self, hp_pct: float, mana_pct: float) -> Optional[str]:
        """Seleciona heal baseado apenas na porcentagem de HP (método tradicional)."""
        # Verificar overheal protection primeiro
        if self.config["enable_overheat_protection"]:
            # Se estiver muito perto do HP máximo, talvez não precise curar
            max_effective_hp = 95  # Não curar se estiver acima de 95% (evita overheal)
            if hp_pct >= max_effective_hp:
                return None
        
        # Seleção tradicional baseada em HP%
        if hp_pct < self.config["hp_ultimate"]:
            if mana_pct > 20 and self._can_cast(self.config["spell_ultimate"]):
                return self.config["spell_ultimate"]
        elif hp_pct < self.config["hp_strong"]:
            if mana_pct > 20 and self._can_cast(self.config["spell_strong"]):
                return self.config["spell_strong"]
        elif hp_pct < self.config["hp_mana_drain"] and mana_pct > self.config["mana_min_for_sd"]:
            if self._can_cast(self.config["spell_mana_drain"]):
                return self.config["spell_mana_drain"]
        elif hp_pct < self.config["hp_light"]:
            if self._can_cast(self.config["spell_light"]):
                return self.config["spell_light"]
                
        return None

    def _can_cast(self, spell: str) -> bool:
        """Verifica se podemos lançar um spell (verificação básica)."""
        # Por enquanto, apenas retornar True - pode ser expandido para verificar
        # cooldowns específicos de spell, requisitos de level, etc.
        return True

    def _execute_heal(self, player: Player, bot_engine, heal_type: str) -> bool:
        """Executa o cura selecionado."""
        try:
            if heal_type == self.config["spell_sacrifice"]:
                # utana vid não precisa de target, é auto-cast
                bot_engine._injector.cast_spell(heal_type)
            else:
                # Outros spells são spells que precisam de target (self)
                bot_engine._injector.cast_spell(heal_type)
            return True
        except Exception as e:
            self._log.error(f"Erro ao casting {heal_type}: {e}")
            return False