"""
Script de auto-attack com Combat AI inteligente.
"""
import time
from typing import Dict, Any, List
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.ai.combat.combat_ai import CombatAI


class AimbotScript(BaseScript):
    """Script de auto-attack com AI de combate."""

    def __init__(self):
        super().__init__("AimBot")
        self.priority = 50
        self.config = {
            "enabled": False,
            "max_distance": 7,
            "attack_hotkey": "F1",
            "min_hp_to_attack": 30,
            "cooldown": 0.3,
            "target_blacklist": ["Training Assistant"],
            "use_combat_ai": True,
        }
        self._last_attack_time = 0
        self._combat_ai = None

    def on_enable(self) -> None:
        """Inicializa Combat AI quando habilitado."""
        super().on_enable()
        if self.config.get("use_combat_ai"):
            # Pega vocação do bot_engine (será passado no context)
            self._log.info("Combat AI será inicializado no primeiro execute")

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

        # Verifica cooldown
        if time.time() - self._last_attack_time < self.config["cooldown"]:
            return False

        # Não ataca se HP muito baixo
        if player.hp_percent() < self.config["min_hp_to_attack"]:
            return False

        # Filtra blacklist
        valid_creatures = [
            c for c in creatures 
            if c.name not in self.config["target_blacklist"]
        ]

        if not valid_creatures:
            return False

        # Usa Combat AI se habilitado
        if self._combat_ai and self.config.get("use_combat_ai"):
            target = self._combat_ai.get_target(player, valid_creatures)
        else:
            # Fallback: usa targeting service padrão
            target = bot_engine._targeting.select_target(
                player,
                valid_creatures,
                bot_engine.config.get("combat_mode", "lowest_hp"),
                self.config["max_distance"],
            )

        if not target:
            return False

        # Ataca
        bot_engine._combat.attack_with_hotkey(target, self.config["attack_hotkey"])
        self._last_attack_time = time.time()
        self._log.info(f"⚔️ Attacking: {target.name} (HP: {target.stats.health}%)")
        
        return True
