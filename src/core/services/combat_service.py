from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.interfaces.injector_interface import ICommandInjector


class CombatService:
    """Serviço que encapsula ações de combate de alto nível."""

    def __init__(self, injector: ICommandInjector) -> None:
        self._injector = injector

    def attack_with_hotkey(self, target: Creature, hotkey: str = "F1") -> None:
        """Ataque genérico usando hotkey (ex: rune, spell em hotkey)."""
        if not target or not target.is_alive():
            return
        self._injector.send_hotkey(hotkey)

    def cast_spell(self, spell_words: str) -> None:
        """Wrapper para lançar spell via injeção."""
        self._injector.cast_spell(spell_words)
