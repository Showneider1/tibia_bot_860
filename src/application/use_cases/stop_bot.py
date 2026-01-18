from src.application.bot_engine import BotEngine


class StopBotUseCase:
    """Caso de uso: Parar automação do bot."""

    def __init__(self, bot_engine: BotEngine):
        self._bot = bot_engine

    def execute(self) -> None:
        self._bot.enabled = False
