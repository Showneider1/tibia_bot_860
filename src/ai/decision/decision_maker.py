"""
Sistema de tomada de decisões baseado em prioridades.
"""
from typing import List, Callable, Optional, Dict
from dataclasses import dataclass
from src.infrastructure.logging.logger import get_logger


@dataclass
class Decision:
    """Representa uma decisão possível."""
    name: str
    priority: int
    condition: Callable[[Dict], bool]
    action: Callable[[Dict], None]


class DecisionMaker:
    """Tomador de decisões baseado em prioridades."""
    
    def __init__(self):
        self.decisions: List[Decision] = []
        self._log = get_logger("DecisionMaker")
    
    def add_decision(self, decision: Decision) -> None:
        """Adiciona decisão."""
        self.decisions.append(decision)
        # Ordena por prioridade (maior = mais importante)
        self.decisions.sort(key=lambda d: d.priority, reverse=True)
    
    def decide(self, context: Dict) -> Optional[str]:
        """
        Toma decisão baseado no contexto.
        
        Returns:
            Nome da decisão tomada ou None
        """
        for decision in self.decisions:
            try:
                if decision.condition(context):
                    self._log.info(f"🎯 Decisão: {decision.name} (prioridade: {decision.priority})")
                    decision.action(context)
                    return decision.name
            except Exception as e:
                self._log.error(f"Erro ao avaliar decisão '{decision.name}': {e}")
        
        return None
    
    def clear_decisions(self) -> None:
        """Limpa todas as decisões."""
        self.decisions.clear()
