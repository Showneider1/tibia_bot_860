from typing import Callable
from .event_types import EventType
from src.infrastructure.logging.logger import get_logger


class EventHandlers:
    """Handlers prontos para eventos comuns."""

    def __init__(self):
        self._log = get_logger("EventHandlers")

    def on_health_low(self, **kwargs) -> None:
        """Handler para HP baixo."""
        hp = kwargs.get("hp", 0)
        hp_max = kwargs.get("hp_max", 1)
        hp_pct = (hp / hp_max) * 100 if hp_max > 0 else 0
        self._log.warning(f"⚠️ HP BAIXO: {hp}/{hp_max} ({hp_pct:.1f}%)")

    def on_mana_low(self, **kwargs) -> None:
        """Handler para mana baixa."""
        mana = kwargs.get("mana", 0)
        mana_pct = kwargs.get("mana_pct", 0)
        self._log.warning(f"⚠️ MANA BAIXA: {mana} ({mana_pct:.1f}%)")

    def on_creature_detected(self, **kwargs) -> None:
        """Handler para criatura detectada."""
        creature_name = kwargs.get("creature_name", "Unknown")
        self._log.info(f"👹 Criatura detectada: {creature_name}")

    def on_level_up(self, **kwargs) -> None:
        """Handler para level up."""
        new_level = kwargs.get("level", 0)
        self._log.info(f"🎉 LEVEL UP! Novo level: {new_level}")

    def on_connection_lost(self, **kwargs) -> None:
        """Handler para perda de conexão."""
        self._log.error("❌ CONEXÃO PERDIDA COM O CLIENTE!")
