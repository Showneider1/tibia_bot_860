"""
Script de auto-attack com Combat AI inteligente e targeting avançado.
Inspirado em ElfBot/WindBot: targeting por experiência, loot value, e combo attacks.
"""
import time
from typing import Dict, Any, List, Optional, Set
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.ai.combat.combat_ai import CombatAI


class AimbotScript(BaseScript):
    """Script de auto-attack com AI de combate e targeting avançado."""

    def __init__(self):
        super().__init__("AimBot")
        self.priority = 50
        self.config = {
            "enabled": False,
            "max_distance": 7,
            "attack_hotkey": "F1",           # Hotkey para attack target
            "min_hp_to_attack": 30,          # HP% mínimo para atacar
            "cooldown": 0.3,                 # Cooldown entre ataques
            "target_blacklist": ["Training Assistant"],
            "target_whitelist": [],           # Se não vazio, apenas estas criaturas
            "use_combat_ai": True,
            
            # Targeting avançado
            "targeting_mode": "highest_xp",   # "highest_xp", "lowest_hp", "closest", "highest_threat"
            "prefer_low_hp_for_kill": True,   # Prioriza criaturas quase mortas para finalizar
            "low_hp_threshold": 25,           # HP% abaixo do qual priorizar (finalizar kill)
            
            # Combo attacks
            "enable_combo_attacks": True,
            "combo_spells": [                  # Sequência de spells para combo
                {"spell": "exori gran", "cooldown": 4.0, "mana_cost": 120, "max_distance": 1},
                {"spell": "exori hur", "cooldown": 6.0, "mana_cost": 40, "max_distance": 3},
            ],
            
            # Priorização por experiência (XP da criatura)
            "xp_values": {                     # XP aproximado por criatura (Tibia 8.60)
                "Dragon": 700,
                "Dragon Lord": 1100,
                "Demon": 6000,
                "Rotworm": 40,
                "Cyclops": 150,
                "Cyclops Smith": 275,
                "Cyclops Drone": 255,
                "Giant Spider": 650,
                "Vampire": 305,
                "Necromancer": 580,
                "Priestess": 420,
            },
            
            # Priorização por loot value
            "loot_values": {                  # Valor médio de loot em gold
                "Dragon": 100,
                "Dragon Lord": 200,
                "Demon": 500,
                "Rotworm": 5,
                "Cyclops": 30,
                "Giant Spider": 80,
            },
            
            # Anti-lure
            "enable_anti_lure": True,
            "max_follow_distance": 10,        # Não seguir criatura além desta distância
            "retreat_distance": 12,           # Recuar se criatura muito longe do ponto de caça
        }
        self._last_attack_time = 0
        self._combat_ai: Optional[CombatAI] = None
        self._current_target: Optional[Creature] = None
        self._combo_index = 0
        self._last_combo_time = 0
        self._combo_cooldowns: Dict[str, float] = {}

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine or not creatures:
            return False

        # Inicializa Combat AI se necessário
        if self.config.get("use_combat_ai") and not self._combat_ai:
            vocation = bot_engine.config.get("player_vocation", "Druid")
            self._combat_ai = CombatAI(vocation)
            self._log.info(f"Combat AI inicializado para {vocation}")

        # Verifica cooldown de attack básico
        if time.time() - self._last_attack_time < self.config["cooldown"]:
            # Mesmo com cooldown de attack, podemos verificar combos
            if self.config["enable_combo_attacks"] and self._current_target:
                return self._try_combo_attack(player, self._current_target, bot_engine)
            return False

        # Não ataca se HP muito baixo
        if player.hp_percent() < self.config["min_hp_to_attack"]:
            return False

        # Filtra criaturas válidas
        valid_creatures = self._filter_creatures(creatures, player)
        if not valid_creatures:
            self._current_target = None
            return False

        # Anti-lure: não seguir criaturas muito longe
        if self.config["enable_anti_lure"]:
            valid_creatures = [
                c for c in valid_creatures
                if player.position.distance_chebyshev(c.position) <= self.config["max_follow_distance"]
            ]
            if not valid_creatures:
                return False

        # Seleciona melhor alvo baseado na estratégia
        target = self._select_target(player, valid_creatures)
        if not target:
            return False

        self._current_target = target

        # Executa ataque
        success = self._attack_target(player, target, bot_engine)
        if success:
            self._last_attack_time = time.time()
            self._log.info(f"⚔️ Atacando: {target.name} (HP: {target.stats.health}%)")
            
            # Tenta combo attack após attack básico
            if self.config["enable_combo_attacks"]:
                self._try_combo_attack(player, target, bot_engine)
            
            return True
            
        return False

    def _filter_creatures(self, creatures: List[Creature], player: Player) -> List[Creature]:
        """Filtra criaturas baseado em blacklist/whitelist e validade."""
        filtered = []
        
        for creature in creatures:
            # Ignora o próprio player
            if creature.id == player.id:
                continue
            
            # Verifica blacklist
            if creature.name in self.config["target_blacklist"]:
                continue
            
            # Se whitelist não está vazia, só permite criaturas na lista
            if self.config["target_whitelist"]:
                if creature.name not in self.config["target_whitelist"]:
                    continue
            
            # Verifica se criatura está viva
            if creature.stats.health <= 0:
                continue
            
            # Verifica distância máxima
            distance = player.position.distance_chebyshev(creature.position)
            if distance > self.config["max_distance"]:
                continue
            
            filtered.append(creature)
        
        return filtered

    def _select_target(self, player: Player, creatures: List[Creature]) -> Optional[Creature]:
        """Seleciona melhor alvo baseado na estratégia configurada."""
        if not creatures:
            return None

        mode = self.config["targeting_mode"]

        # Se temos alvo atual e ainda é válido, mantém (evita troca constante)
        if self._current_target and self._current_target in creatures:
            current_distance = player.position.distance_chebyshev(self._current_target.position)
            # Mantém alvo se ainda está vivo e dentro da distância
            if (self._current_target.stats.health > 0 and 
                current_distance <= self.config["max_distance"]):
                # A menos que tenha criatura quase morta que devamos finalizar
                if self.config["prefer_low_hp_for_kill"]:
                    low_hp_target = self._find_low_hp_target(creatures)
                    if low_hp_target and low_hp_target != self._current_target:
                        return low_hp_target
                return self._current_target

        # Seleção baseada no modo
        if mode == "highest_xp":
            return self._select_highest_xp(creatures)
        elif mode == "lowest_hp":
            return self._select_lowest_hp(creatures)
        elif mode == "closest":
            return self._select_closest(player, creatures)
        elif mode == "highest_threat":
            if self._combat_ai:
                return self._combat_ai.get_target(player, creatures)
            return self._select_highest_threat(player, creatures)
        else:
            # Fallback: primeiro válido
            return creatures[0]

    def _select_highest_xp(self, creatures: List[Creature]) -> Optional[Creature]:
        """Seleciona criatura que dá mais XP."""
        xp_values = self.config.get("xp_values", {})
        
        # Se não temos valores de XP, usa HP como proxy
        if not xp_values:
            return max(creatures, key=lambda c: c.stats.max_health)
        
        return max(creatures, key=lambda c: xp_values.get(c.name, c.stats.max_health))

    def _select_lowest_hp(self, creatures: List[Creature]) -> Optional[Creature]:
        """Seleciona criatura com menor HP para finalizar kill."""
        return min(creatures, key=lambda c: c.stats.health)

    def _find_low_hp_target(self, creatures: List[Creature]) -> Optional[Creature]:
        """Encontra criatura com HP baixo para finalizar."""
        threshold = self.config["low_hp_threshold"]
        low_hp_creatures = [c for c in creatures if c.stats.health <= threshold]
        if not low_hp_creatures:
            return None
        return min(low_hp_creatures, key=lambda c: c.stats.health)

    def _select_closest(self, player: Player, creatures: List[Creature]) -> Optional[Creature]:
        """Seleciona criatura mais próxima."""
        return min(creatures, key=lambda c: player.position.distance_chebyshev(c.position))

    def _select_highest_threat(self, player: Player, creatures: List[Creature]) -> Optional[Creature]:
        """Seleciona criatura com maior ameaça (fallback sem CombatAI)."""
        # Calcula ameaça simples: distância + HP
        def threat_score(c):
            distance = player.position.distance_chebyshev(c.position)
            # Mais perto = mais ameaça
            distance_score = max(0, 10 - distance)
            # Mais HP = mais ameaça
            hp_score = c.stats.health / 10
            return distance_score + hp_score
        
        return max(creatures, key=threat_score)

    def _attack_target(self, player: Player, target: Creature, bot_engine) -> bool:
        """Executa ataque ao alvo."""
        try:
            bot_engine._injector.send_hotkey(self.config["attack_hotkey"])
            return True
        except Exception as e:
            self._log.error(f"Erro ao atacar {target.name}: {e}")
            return False

    def _try_combo_attack(self, player: Player, target: Creature, bot_engine) -> bool:
        """Tenta executar combo attack se disponível."""
        if not self.config["enable_combo_attacks"]:
            return False
            
        combo_spells = self.config.get("combo_spells", [])
        if not combo_spells:
            return False
        
        current_time = time.time()
        
        for combo in combo_spells:
            spell_name = combo["spell"]
            cooldown = combo.get("cooldown", 0)
            mana_cost = combo.get("mana_cost", 0)
            max_distance = combo.get("max_distance", 1)
            
            # Verifica cooldown do spell
            last_use = self._combo_cooldowns.get(spell_name, 0)
            if current_time - last_use < cooldown:
                continue
            
            # Verifica mana
            if player.stats.mana < mana_cost:
                continue
            
            # Verifica distância
            distance = player.position.distance_chebyshev(target.position)
            if distance > max_distance:
                continue
            
            # Executa combo spell
            try:
                bot_engine._injector.cast_spell(spell_name)
                self._combo_cooldowns[spell_name] = current_time
                self._log.info(f"💥 Combo: {spell_name} em {target.name}")
                return True
            except Exception as e:
                self._log.error(f"Erro ao executar combo {spell_name}: {e}")
        
        return False

    def clear_target(self) -> None:
        """Limpa o alvo atual."""
        self._current_target = None

    def get_current_target(self) -> Optional[Creature]:
        """Retorna alvo atual."""
        return self._current_target