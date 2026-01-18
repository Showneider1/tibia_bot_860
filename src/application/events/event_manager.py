from typing import Callable, Dict, List
from collections import defaultdict
from .event_types import EventType
from src.infrastructure.logging.logger import get_logger


class EventManager:
    """Gerenciador de eventos (Observer Pattern)."""

    def __init__(self):
        self._listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self._log = get_logger("EventManager")

    def subscribe(self, event: EventType, callback: Callable) -> None:
        self._listeners[event].append(callback)
        self._log.debug(f"Listener registrado para {event.value}")

    def unsubscribe(self, event: EventType, callback: Callable) -> None:
        if callback in self._listeners[event]:
            self._listeners[event].remove(callback)

    def emit(self, event: EventType, **kwargs) -> None:
        self._log.debug(f"Evento disparado: {event.value}")
        for callback in self._listeners[event]:
            try:
                callback(**kwargs)
            except Exception as e:
                self._log.error(f"Erro no callback de {event.value}: {e}")
