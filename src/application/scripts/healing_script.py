import time
from typing import Dict, Any
from .base_script import BaseScript
from src.core.entities.player import Player


class HealingScript(BaseScript):
    """Script de auto-healing inteligente."""

    def __init__(self):
        super().__init__("HealingBot")
        self.priority = 100  # Máxima prioridade
        self.config = {
            "hp_threshold": 50,      # % de HP para curar
            "mana_threshold": 20,    # % mana mínima para curar
            "spell_light": "exura",
            "spell_strong": "exura gran",
            "spell_ultimate": "exura vita",
            "hp_light": 80,          # Usa light heal acima de 80%
            "hp_strong": 50,         # Usa strong heal entre 50-80%
            "cooldown": 1.0,         # Cooldown entre heals (segundos)
        }
        self._last_heal_time = 0

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        # Verifica cooldown
        if time.time() - self._last_heal_time < self.config["cooldown"]:
            return False

        hp_pct = player.hp_percent()
        mana_pct = player.mana_percent()

        # Precisa curar?
        if hp_pct >= self.config["hp_threshold"]:
            return False

        # Tem mana?
        if mana_pct < self.config["mana_threshold"]:
            self._log.warning("Mana baixa, não pode curar!")
            return False

        # Seleciona spell baseado no HP
        spell = self._select_heal_spell(hp_pct)
        
        # Lança spell
        bot_engine._combat.cast_spell(spell)
        self._last_heal_time = time.time()
        self._log.info(f"🩹 Healing com '{spell}' (HP: {hp_pct:.1f}%)")
        
        return True

    def _select_heal_spell(self, hp_pct: float) -> str:
        """Seleciona spell apropriada baseado no HP%."""
        if hp_pct > self.config["hp_light"]:
            return self.config["spell_light"]
        elif hp_pct > self.config["hp_strong"]:
            return self.config["spell_strong"]
        else:
            return self.config["spell_ultimate"]
