from src.core.entities.spell import Spell

# Spells de cura comuns; podem ser expandidos
HEALING_SPELLS = {
    "light": Spell(name="Light Healing", words="exura", mana_cost=25, cooldown_ms=1000),
    "strong": Spell(name="Intense Healing", words="exura gran", mana_cost=70, cooldown_ms=1000),
    "very_strong": Spell(name="Ultimate Healing", words="exura vita", mana_cost=160, cooldown_ms=1000),
}
