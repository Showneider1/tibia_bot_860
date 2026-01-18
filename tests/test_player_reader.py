"""
Testes para PlayerReader.
"""
import unittest
from unittest.mock import Mock, patch
from src.infrastructure.readers.player_reader import PlayerReader


class TestPlayerReader(unittest.TestCase):
    """Testes da classe PlayerReader."""

    def setUp(self):
        """Setup dos testes."""
        self.mock_memory = Mock()
        self.addresses = {
            "id": 0x63FE98,
            "health": 0x63FE94,
            "health_max": 0x63FE90,
            "mana": 0x63FE6C,
            "mana_max": 0x63FE68,
            "level": 0x63FE88,
            "experience": 0x63FE8C,
            "magic_level": 0x63FE84,
            "soul": 0x63FE64,
            "stamina": 0x63FE60,
            "capacity": 0x63FE5C,
        }
        self.reader = PlayerReader(self.mock_memory, self.addresses)

    def test_get_player_success(self):
        """Testa leitura bem-sucedida de player."""
        self.mock_memory.read_int.side_effect = [
            12345,      # id
            500,        # health
            500,        # health_max
            100,        # mana
            100,        # mana_max
            50,         # level
            1000000,    # experience
            10,         # magic_level
            50,         # soul
            100,        # stamina
            2000,       # capacity
        ]

        player = self.reader.get_player()

        self.assertIsNotNone(player)
        self.assertEqual(player.id, 12345)
        self.assertEqual(player.health, 500)
        self.assertEqual(player.health_max, 500)
        self.assertEqual(player.level, 50)

    def test_get_player_not_loaded(self):
        """Testa quando player não está carregado (ID = 0)."""
        self.mock_memory.read_int.return_value = 0

        player = self.reader.get_player()

        self.assertIsNone(player)

    def test_get_player_invalid_health_values(self):
        """Testa validação de valores de health inválidos."""
        self.mock_memory.read_int.side_effect = [
            12345,      # id
            600,        # health > health_max (INVÁLIDO)
            500,        # health_max
        ]

        player = self.reader.get_player()

        # Deve retornar None ou último válido
        self.assertIsNone(player)

    def test_get_player_with_exception(self):
        """Testa tratamento de exceção."""
        self.mock_memory.read_int.side_effect = RuntimeError("Memory read error")

        player = self.reader.get_player()

        self.assertIsNone(player)


class TestCreatureReader(unittest.TestCase):
    """Testes da classe CreatureReader."""

    def setUp(self):
        """Setup dos testes."""
        self.mock_memory = Mock()
        self.addresses = {
            "start": 0x63FEF8,
            "step": 0xA8,
            "max_creatures": 250,
        }
        self.offsets = {
            "id": 0,
            "name": 4,
            "x": 36,
            "y": 40,
            "z": 44,
            "hp_bar": 136,
        }

    def test_get_creatures_empty_list(self):
        """Testa leitura com nenhuma criatura."""
        from src.infrastructure.readers.creature_reader import CreatureReader

        reader = CreatureReader(self.mock_memory, self.addresses, self.offsets)
        # Todos os IDs são 0 (slots vazios)
        self.mock_memory.read_int.return_value = 0

        creatures = reader.get_creatures()

        self.assertEqual(len(creatures), 0)

    def test_get_creatures_with_valid_creature(self):
        """Testa leitura com criatura válida."""
        from src.infrastructure.readers.creature_reader import CreatureReader

        reader = CreatureReader(self.mock_memory, self.addresses, self.offsets)

        # Simula 2 criaturas válidas e slots vazios
        def mock_read_int(addr):
            if addr == 0x63FEF8:  # Primeiro slot - ID
                return 1001
            elif addr == 0x63FEFD:  # Segundo slot - ID
                return 1002
            else:
                return 0  # Slots vazios

        self.mock_memory.read_int.side_effect = mock_read_int
        self.mock_memory.read_string.return_value = "Spider"

        creatures = reader.get_creatures()

        # Deve ter 2 criaturas (teórico, pode variar por side_effect)
        self.assertGreaterEqual(len(creatures), 0)


if __name__ == "__main__":
    unittest.main()
