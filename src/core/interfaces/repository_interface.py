from abc import ABC, abstractmethod
from typing import Any


class IRepository(ABC):
    """Contrato genérico de repositório."""

    @abstractmethod
    def load(self, key: str) -> Any:
        ...

    @abstractmethod
    def save(self, key: str, value: Any) -> None:
        ...
