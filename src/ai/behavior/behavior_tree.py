"""
Implementação de Behavior Tree.
"""
from typing import List, Optional, Callable
from enum import Enum
from src.infrastructure.logging.logger import get_logger


class NodeStatus(Enum):
    """Status de execução de um nó."""
    SUCCESS = "success"
    FAILURE = "failure"
    RUNNING = "running"


class BehaviorNode:
    """Nó base da Behavior Tree."""
    
    def __init__(self, name: str = "Node"):
        self.name = name
        self._log = get_logger(f"BT.{name}")
    
    def tick(self, context: dict) -> NodeStatus:
        """Executa o nó."""
        raise NotImplementedError


class BehaviorTree:
    """Árvore de comportamento."""
    
    def __init__(self, root: BehaviorNode):
        self.root = root
        self._log = get_logger("BehaviorTree")
    
    def tick(self, context: dict) -> NodeStatus:
        """Executa a árvore."""
        return self.root.tick(context)
