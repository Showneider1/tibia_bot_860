"""
Script de auto-healing avancado com multiplas estrategias.
"""
import time
from typing import Dict, Any, Optional
from .base_script import BaseScript
from src.core.entities.player import Player


class HealingScript(BaseScript):
    """Script de auto-healing avancado com multiplas estrategias."""

    def __init__(self):
        super().__init__("HealingBot")
        self.priority = 100  # Maxima prioridade
        self.config = {
            # Healing baseado em porcentagem de HP (metodo tradicional)
            "hp_threshold": 50,
            "mana_threshold": 20,

            # Healing baseado em dano recebido (metodo avancado)
            "enable_dps_healing": True,
            "dps_threshold": 80,
            "dps_window": 2.0,

            # Spells disponiveis
            "spell_light":      "exura",
            "spell_strong":     "exura gran",
            "spell_ultimate":   "exura vita",
            "spell_mana_drain": "exura sio",
            "spell_sacrifice":  "utana vid",

            # Configuracoes de cada spell
            "hp_light":          85,
            "hp_strong":         50,
            "hp_ultimate":       25,
            "hp_mana_drain":     40,
            "mana_min_for_sd":   25,

            # Sacrifice
            "enable_sacrifice":          True,
            "sacrifice_hp_threshold":    15,
            "sacrifice_mana_threshold":  40,

            # Protecao contra overheal
            "enable_overheat_protection": True,
            "overheat_threshold":          0.9,

            # Cooldowns e timing
            "cooldown":       0.8,
            "last_heal_time": 0,
        }
        # --- atributos internos inicializados corretamente ---
        self._last_hp: int        = 0
        self._last_dps_check: float = 0.0
        self._current_dps: float  = 0.0   # FIX: inicializado para evitar AttributeError

    # ------------------------------------------------------------------
    # Ponto de entrada principal
    # ------------------------------------------------------------------

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player    = context.get("player")
        bot_engine        = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        current_time = time.time()
        self._update_dps_tracking(player, current_time)

        if current_time - self.config["last_heal_time"] < self.config["cooldown"]:
            return False

        should_heal, heal_type, reason = self._should_heal(player)
        if not should_heal:
            return False

        success = self._execute_heal(player, bot_engine, heal_type)
        if success:
            self.config["last_heal_time"] = current_time
            self._log.info(
                f"Healing com '{heal_type}' ({reason}) - HP: {player.hp_percent():.1f}%"
            )
            return True

        return False

    # ------------------------------------------------------------------
    # Tracking de DPS
    # ------------------------------------------------------------------

    def _update_dps_tracking(self, player: Player, current_time: float) -> None:
        """Atualiza o tracking de HP para calculo de dano por segundo."""
        if self._last_hp > 0 and self._last_dps_check > 0:
            time_diff = current_time - self._last_dps_check
            if time_diff > 0:
                hp_lost = max(0, self._last_hp - player.stats.health)
                self._current_dps = (hp_lost / time_diff) if hp_lost > 0 else 0.0
            else:
                self._current_dps = 0.0
        else:
            self._current_dps = 0.0

        self._last_hp          = player.stats.health
        self._last_dps_check   = current_time

    # ------------------------------------------------------------------
    # Decisao de cura
    # ------------------------------------------------------------------

    def _should_heal(self, player: Player) -> tuple:
        """
        Determina se deve curar e qual tipo de heal usar.
        Returns: (should_heal, heal_type, reason)
        """
        hp_pct   = player.hp_percent()
        mana_pct = player.mana_percent()

        if hp_pct >= 100:
            return False, None, "HP cheio"

        if mana_pct < self.config["mana_threshold"]:
            return False, None, f"Mana baixa ({mana_pct:.1f}%)"

        # Healing baseado em DPS
        if self.config["enable_dps_healing"] and self._current_dps > self.config["dps_threshold"]:
            heal_type = self._select_heal_by_urgency(hp_pct, mana_pct, self._current_dps)
            if heal_type:
                return True, heal_type, f"DPS alto ({self._current_dps:.1f} HP/s)"

        # Healing tradicional por % HP
        heal_type = self._select_heal_by_hp_percentage(hp_pct, mana_pct)
        if heal_type:
            return True, heal_type, f"HP baixo ({hp_pct:.1f}%)"

        # Sacrifice como ultimo recurso
        if (
            self.config["enable_sacrifice"]
            and hp_pct   < self.config["sacrifice_hp_threshold"]
            and mana_pct > self.config["sacrifice_mana_threshold"]
        ):
            return True, self.config["spell_sacrifice"], "Emergencia - Sacrifice"

        return False, None, "Nao precisa de cura"

    def _select_heal_by_urgency(
        self, hp_pct: float, mana_pct: float, dps: float
    ) -> Optional[str]:
        """Seleciona heal baseado na urgencia (DPS + HP%)."""
        if dps > 200 and hp_pct < 20:
            if mana_pct > 20 and self._can_cast(self.config["spell_ultimate"]):
                return self.config["spell_ultimate"]
            if self.config["enable_sacrifice"] and mana_pct > self.config["sacrifice_mana_threshold"]:
                return self.config["spell_sacrifice"]

        if dps > 100 and hp_pct < 40:
            if mana_pct > 25 and self._can_cast(self.config["spell_strong"]):
                return self.config["spell_strong"]
            if self._can_cast(self.config["spell_light"]):
                return self.config["spell_light"]

        if dps > 50 and hp_pct < 60:
            if mana_pct > 30 and self._can_cast(self.config["spell_mana_drain"]):
                return self.config["spell_mana_drain"]
            if self._can_cast(self.config["spell_strong"]):
                return self.config["spell_strong"]

        return None

    def _select_heal_by_hp_percentage(
        self, hp_pct: float, mana_pct: float
    ) -> Optional[str]:
        """Seleciona heal baseado apenas na porcentagem de HP."""
        threshold = int(self.config["overheat_threshold"] * 100)
        if self.config["enable_overheat_protection"] and hp_pct >= threshold:
            return None

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
        """Verifica se podemos lancar um spell."""
        return bool(spell)

    # ------------------------------------------------------------------
    # Execucao do heal — FIX: usa metodo publico do engine
    # ------------------------------------------------------------------

    def _execute_heal(self, player: Player, bot_engine, heal_type: str) -> bool:
        """
        Executa o heal selecionado via bot_engine.cast_spell() (método público).
        """
        try:
            bot_engine.cast_spell(heal_type)
            return True
        except Exception as e:
            self._log.error(f"Erro ao casting {heal_type}: {e}")
            return False
