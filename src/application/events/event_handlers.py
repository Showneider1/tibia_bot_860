from typing import Callable
from .event_types import EventType
from src.infrastructure.logging.logger import get_logger


class EventHandlers:
    """Handlers prontos para eventos comuns."""

    def __init__(self):
        self._log = get_logger("EventHandlers")

    def on_health_low(self, **kwargs) -> None:
        player = kwargs.get("player")
        if player is None:
            return
        hp = player.stats.health
        hp_max = player.stats.max_health
        hp_pct = (hp / hp_max) * 100 if hp_max > 0 else 0
        self._log.warning(f"HP BAIXO: {hp}/{hp_max} ({hp_pct:.1f}%)")

    def on_mana_low(self, **kwargs) -> None:
        player = kwargs.get("player")
        if player is None:
            return
        mana = player.stats.mana
        mana_max = player.stats.max_mana
        mana_pct = (mana / mana_max) * 100 if mana_max > 0 else 0
        self._log.warning(f"MANA BAIXA: {mana}/{mana_max} ({mana_pct:.1f}%)")

    def on_creature_detected(self, **kwargs) -> None:
        creature = kwargs.get("creature")
        if creature is None:
            return
        self._log.info(f"Criatura detectada: {creature.name}")

    def on_level_up(self, **kwargs) -> None:
        player = kwargs.get("player")
        if player is None:
            return
        self._log.info(f"LEVEL UP! Novo level: {player.level}")

    def on_connection_lost(self, **kwargs) -> None:
        self._log.error("CONEXAO PERDIDA COM O CLIENTE!")
