import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.creature import Creature


@dataclass
class PersistentRule:
    name: str = ""
    enabled: bool = True
    condition_type: str = "always"
    condition_params: Dict[str, Any] = field(default_factory=dict)
    action_type: str = "log"
    action_params: Dict[str, Any] = field(default_factory=dict)
    cooldown: float = 1.0
    last_run: float = 0.0


_CONDITION_DESCRIPTIONS = {
    "always": "Sempre (incondicional)",
    "hp_below": "HP do player abaixo de %",
    "mana_below": "Mana do player abaixo de %",
    "hp_above": "HP do player acima de %",
    "mana_above": "Mana do player acima de %",
    "creature_nearby": "Criatura especifica por perto",
    "creature_count_min": "Total de criaturas >= N",
    "creature_count_max": "Total de criaturas <= N",
    "has_item": "Item no inventario (ID)",
    "level_above": "Level do player acima de",
    "level_below": "Level do player abaixo de",
    "vocation_is": "Vocacao do player e",
}

_ACTION_DESCRIPTIONS = {
    "cast": "Executar spell (exori gran)",
    "say": "Falar no chat",
    "hotkey": "Pressionar hotkey (F1-F12)",
    "log": "Escrever no log",
    "use_item": "Usar item (hotkey)",
    "pause_cavebot": "Pausar cavebot por N segundos",
    "enable_rule": "Ativar outra regra (nome)",
    "disable_rule": "Desativar outra regra (nome)",
}

_ACTION_PARAM_LABELS = {
    "cast": {"spell": "Palavras magicas:"},
    "say": {"text": "Mensagem:"},
    "hotkey": {"key": "Tecla (F1-F12):"},
    "log": {"message": "Mensagem:"},
    "use_item": {"hotkey": "Hotkey:"},
    "pause_cavebot": {"seconds": "Segundos:"},
    "enable_rule": {"rule_name": "Nome da regra:"},
    "disable_rule": {"rule_name": "Nome da regra:"},
}

_CONDITION_PARAM_LABELS = {
    "hp_below": {"pct": "HP% abaixo de:"},
    "mana_below": {"pct": "Mana% abaixo de:"},
    "hp_above": {"pct": "HP% acima de:"},
    "mana_above": {"pct": "Mana% acima de:"},
    "creature_nearby": {"name": "Nome:", "distance": "Distancia (sqm):"},
    "creature_count_min": {"count": "Minimo:"},
    "creature_count_max": {"count": "Maximo:"},
    "has_item": {"item_id": "ID do item:"},
    "level_above": {"level": "Level acima de:"},
    "level_below": {"level": "Level abaixo de:"},
    "vocation_is": {"vocation": "Vocacao:"},
}


class PersistentScript(BaseScript):
    """Sistema estilo ElfBot Persistent — regras customizaveis com condicao + acao."""

    def __init__(self):
        super().__init__("Persistent")
        self.priority = 40
        self.config = {
            "rules": [],
        }

    def check_condition(self, rule: PersistentRule, player: Player, creatures: List[Creature]) -> bool:
        ct = rule.condition_type
        cp = rule.condition_params

        if ct == "always":
            return True

        if ct == "hp_below":
            return player.hp_percent() < float(cp.get("pct", 50))
        if ct == "hp_above":
            return player.hp_percent() > float(cp.get("pct", 50))

        if ct == "mana_below":
            return player.mana_percent() < float(cp.get("pct", 20))
        if ct == "mana_above":
            return player.mana_percent() > float(cp.get("pct", 20))

        if ct in ("creature_nearby",):
            name = cp.get("name", "").strip().lower()
            dist = int(cp.get("distance", 5))
            if not name:
                return False
            for c in creatures:
                if c.name.lower() == name:
                    d = player.position.distance_chebyshev(c.position) if player.position and c.position else 999
                    if d <= dist:
                        return True
            return False

        if ct == "creature_count_min":
            return len(creatures) >= int(cp.get("count", 1))

        if ct == "creature_count_max":
            return len(creatures) <= max(0, int(cp.get("count", 0)))

        if ct == "has_item":
            return False

        if ct == "level_above":
            return player.level >= int(cp.get("level", 100))
        if ct == "level_below":
            return player.level < int(cp.get("level", 100))

        if ct == "vocation_is":
            return player.vocation.lower() == cp.get("vocation", "").lower().strip()

        return False

    def execute_action(self, rule: PersistentRule, bot_engine) -> bool:
        at = rule.action_type
        ap = rule.action_params

        try:
            if at == "cast":
                bot_engine.cast_spell(ap.get("spell", ""))
                return True
            if at == "say":
                bot_engine.injector.say(ap.get("text", ""))
                return True
            if at == "hotkey":
                bot_engine.injector.send_hotkey(ap.get("key", "F1"))
                return True
            if at == "log":
                self._log.info(f"[Persistent] {ap.get('message', '')}")
                return True
            if at == "use_item":
                bot_engine.injector.send_hotkey(ap.get("hotkey", "F1"))
                return True
            if at == "pause_cavebot":
                script = bot_engine.script_engine.get_script("CaveBot")
                if script:
                    script.enabled = False
                    delay = float(ap.get("seconds", 5))
                    self._pause_until = time.time() + delay
                return True
            if at == "enable_rule":
                return self._toggle_rule(ap.get("rule_name", ""), True)
            if at == "disable_rule":
                return self._toggle_rule(ap.get("rule_name", ""), False)
        except Exception as e:
            self._log.error(f"Erro executando acao '{at}': {e}")
        return False

    def _toggle_rule(self, name: str, enabled: bool) -> bool:
        for rule in self.config.get("rules", []):
            if isinstance(rule, dict) and rule.get("name", "").lower() == name.lower():
                rule["enabled"] = enabled
                self._log.info(f"Regra '{name}' {'ativada' if enabled else 'desativada'}")
                return True
            if isinstance(rule, PersistentRule) and rule.name.lower() == name.lower():
                rule.enabled = enabled
                self._log.info(f"Regra '{name}' {'ativada' if enabled else 'desativada'}")
                return True
        return False

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        now = time.time()
        rules: list = self.config.get("rules", [])
        executed = False

        for i, rule_data in enumerate(rules):
            if isinstance(rule_data, dict):
                rule = PersistentRule(**rule_data)
            elif isinstance(rule_data, PersistentRule):
                rule = rule_data
            else:
                continue

            if not rule.enabled:
                continue
            if now - rule.last_run < rule.cooldown:
                continue

            if self.check_condition(rule, player, creatures):
                self.execute_action(rule, bot_engine)
                rule.last_run = now
                if isinstance(rules[i], dict):
                    rules[i]["last_run"] = now
                executed = True

        return executed

    def get_condition_descriptions(self) -> Dict[str, str]:
        return dict(_CONDITION_DESCRIPTIONS)

    def get_action_descriptions(self) -> Dict[str, str]:
        return dict(_ACTION_DESCRIPTIONS)

    def get_condition_params(self, ct: str) -> Dict[str, str]:
        return dict(_CONDITION_PARAM_LABELS.get(ct, {}))

    def get_action_params(self, at: str) -> Dict[str, str]:
        return dict(_ACTION_PARAM_LABELS.get(at, {}))
