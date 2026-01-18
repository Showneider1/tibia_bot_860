from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseCondition(ABC):
    """Classe base para condições."""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """
        Avalia se condição é verdadeira.
        
        Args:
            context: Contexto com player, creatures, etc.
            
        Returns:
            True se condição atendida
        """
        pass
