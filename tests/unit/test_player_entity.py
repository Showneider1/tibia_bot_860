import unittest
from src.core.entities.player import Player
from src.core.value_objects.position import Position
from src.core.value_objects.stats import Stats


class TestPlayerEntity(unittest.TestCase):
    """Testes para entidade Player."""

    def test_hp_percent_zero_max_health(self):
        """Quando max_health for zero, hp_percent deve retornar 0.0."""
        player = Player(
            id=1,
            name="Test",
            position=Position(0, 0, 0),
            stats=Stats(health=100, max_health=0, mana=50, max_mana=100),
            level=1,
            experience=0,
            magic_level=0,
            soul=0,
            stamina=0,
            capacity=0,
        )
        self.assertEqual(player.hp_percent(), 0.0)

    def test_hp_percent_normal(self):
        """hp_percent deve retornar porcentagem correta."""
        player = Player(
            id=1,
            name="Test",
            position=Position(0, 0, 0),
            stats=Stats(health=50, max_health=100, mana=30, max_mana=60),
            level=1,
            experience=0,
            magic_level=0,
            soul=0,
            stamina=0,
            capacity=0,
        )
        self.assertEqual(player.hp_percent(), 50.0)

    def test_mana_percent_zero_max_mana(self):
        """Quando max_mana for zero, mana_percent deve retornar 0.0."""
        player = Player(
            id=1,
            name="Test",
            position=Position(0, 0, 0),
            stats=Stats(health=100, max_health=100, mana=50, max_mana=0),
            level=1,
            experience=0,
            magic_level=0,
            soul=0,
            stamina=0,
            capacity=0,
        )
        self.assertEqual(player.mana_percent(), 0.0)

    def test_mana_percent_normal(self):
        """mana_percent deve retornar porcentagem correta."""
        player = Player(
            id=1,
            name="Test",
            position=Position(0, 0, 0),
            stats=Stats(health=100, max_health=100, mana=30, max_mana=60),
            level=1,
            experience=0,
            magic_level=0,
            soul=0,
            stamina=0,
            capacity=0,
        )
        self.assertEqual(player.mana_percent(), 50.0)

    def test_is_alive(self):
        """is_alive deve retornar True se health > 0."""
        player_alive = Player(
            id=1,
            name="Test",
            position=Position(0, 0, 0),
            stats=Stats(health=1, max_health=100, mana=0, max_mana=0),
            level=1,
            experience=0,
            magic_level=0,
            soul=0,
            stamina=0,
            capacity=0,
        )
        player_dead = Player(
            id=2,
            name="Test",
            position=Position(0, 0, 0),
            stats=Stats(health=0, max_health=100, mana=0, max_mana=0),
            level=1,
            experience=0,
            magic_level=0,
            soul=0,
            stamina=0,
            capacity=0,
        )
        self.assertTrue(player_alive.is_alive())
        self.assertFalse(player_dead.is_alive())


if __name__ == '__main__':
    unittest.main()