from src.application.bot_engine import BotEngine


class CastSpellUseCase:
    """Caso de uso: Lançar spell manualmente."""

    def __init__(self, bot_engine: BotEngine):
        self._bot = bot_engine

    def execute(self, spell_words: str) -> None:
        self._bot._combat.cast_spell(spell_words)
