from src.application.bot_engine import BotEngine


class ConnectBotUseCase:
    """Caso de uso: Conectar ao processo Tibia."""

    def __init__(self, bot_engine: BotEngine):
        self._bot = bot_engine

    def execute(self) -> bool:
        return self._bot.start()
