import unittest
from unittest.mock import Mock
from src.application.events.event_manager import EventManager
from src.application.events.event_types import EventType


class TestEventManager(unittest.TestCase):
    """Testes para EventManager."""

    def setUp(self):
        self.em = EventManager()

    def test_subscribe_and_emit(self):
        """Deve permitir inscrição e emissão de eventos."""
        callback = Mock()
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, callback)

        self.em.emit(EventType.PLAYER_HEALTH_LOW, player="test")

        callback.assert_called_once_with(player="test")

    def test_multiple_subscribers(self):
        """Deve chamar todos os inscritos para um evento."""
        cb1 = Mock()
        cb2 = Mock()
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, cb1)
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, cb2)

        self.em.emit(EventType.PLAYER_HEALTH_LOW, player="x")

        cb1.assert_called_once_with(player="x")
        cb2.assert_called_once_with(player="x")

    def test_unsubscribe(self):
        """Deve remover inscrição específica."""
        callback = Mock()
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, callback)
        self.em.unsubscribe(EventType.PLAYER_HEALTH_LOW, callback)

        self.em.emit(EventType.PLAYER_HEALTH_LOW, player="x")
        callback.assert_not_called()

    def test_event_isolation(self):
        """Eventos diferentes não devem disparar callbacks errados."""
        callback = Mock()
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, callback)

        self.em.emit(EventType.PLAYER_MANA_LOW, player="x")
        callback.assert_not_called()

    def test_exception_in_callback_does_not_break_others(self):
        """Se um callback lançar exceção, os outros devem ser chamados."""
        def bad_callback(**kwargs):
            raise ValueError("bad")

        good_callback = Mock()
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, bad_callback)
        self.em.subscribe(EventType.PLAYER_HEALTH_LOW, good_callback)

        # Should not raise
        self.em.emit(EventType.PLAYER_HEALTH_LOW, player="x")
        good_callback.assert_called_once_with(player="x")


if __name__ == '__main__':
    unittest.main()