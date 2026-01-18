import time
from typing import Any


class MemoryCache:
    """Cache simples com TTL para leituras de memória."""

    def __init__(self, ttl: float = 0.05) -> None:
        self._ttl = ttl
        self._values: dict[int, Any] = {}
        self._timestamps: dict[int, float] = {}

    def get(self, address: int) -> Any | None:
        now = time.time()
        ts = self._timestamps.get(address)
        if ts is None:
            return None
        if now - ts > self._ttl:
            self._values.pop(address, None)
            self._timestamps.pop(address, None)
            return None
        return self._values.get(address)

    def set(self, address: int, value: Any) -> None:
        self._values[address] = value
        self._timestamps[address] = time.time()

    def clear(self) -> None:
        self._values.clear()
        self._timestamps.clear()
