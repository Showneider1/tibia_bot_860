import unittest
from dataclasses import FrozenInstanceError
from src.core.value_objects.address import MemoryAddress


class TestMemoryAddress(unittest.TestCase):
    """Testes para MemoryAddress."""

    def test_addition(self):
        addr = MemoryAddress(100)
        result = addr + 50
        self.assertIsInstance(result, MemoryAddress)
        self.assertEqual(result.value, 150)

    def test_reverse_addition(self):
        addr = MemoryAddress(100)
        result = 50 + addr
        self.assertIsInstance(result, MemoryAddress)
        self.assertEqual(result.value, 150)

    def test_subtraction(self):
        addr = MemoryAddress(100)
        result = addr - 30
        self.assertIsInstance(result, MemoryAddress)
        self.assertEqual(result.value, 70)

    def test_with_offset(self):
        addr = MemoryAddress(0x63FE8C)
        result = addr.with_offset(12)
        self.assertIsInstance(result, MemoryAddress)
        self.assertEqual(result.value, 0x63FE98)

    def test_immutable(self):
        addr = MemoryAddress(100)
        with self.assertRaises(FrozenInstanceError):
            addr.value = 200


if __name__ == '__main__':
    unittest.main()