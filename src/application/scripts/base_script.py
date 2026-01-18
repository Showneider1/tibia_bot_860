from abc import ABC, abstractmethod
from typing import Dict, Any
from src.infrastructure.logging.logger import get_logger


class BaseScript(ABC):
    """Classe base para todos os scripts do bot."""

    def __init__(self, name: str):
        self.name = name
        self.enabled = False
        self.priority = 0  # Maior = executa primeiro
        self._log = get_logger(f"Script.{name}")
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> bool:
        """
        Executa o script.
        
        Args:
            context: Dicionário com player, creatures, bot_engine, etc.
            
        Returns:
            True se executou ação, False se não fez nada
        """
        pass

    def on_enable(self) -> None:
        """Chamado quando script é habilitado."""
        self._log.info(f"Script '{self.name}' habilitado.")

    def on_disable(self) -> None:
        """Chamado quando script é desabilitado."""
        self._log.info(f"Script '{self.name}' desabilitado.")

    def validate_config(self) -> bool:
        """Valida configuração do script."""
        return True
