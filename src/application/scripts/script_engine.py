import time
from typing import List, Dict, Any
from .base_script import BaseScript
from src.infrastructure.logging.logger import get_logger


class ScriptEngine:
    """Motor de execução de scripts."""

    def __init__(self):
        self._scripts: List[BaseScript] = []
        self._log = get_logger("ScriptEngine")

    def register(self, script: BaseScript) -> None:
        """Registra um script."""
        self._scripts.append(script)
        self._scripts.sort(key=lambda s: s.priority, reverse=True)
        self._log.info(f"Script '{script.name}' registrado (prioridade: {script.priority})")

    def unregister(self, script_name: str) -> None:
        """Remove um script."""
        self._scripts = [s for s in self._scripts if s.name != script_name]
        self._log.info(f"Script '{script_name}' removido.")

    def enable_script(self, script_name: str) -> bool:
        """Habilita um script específico."""
        for script in self._scripts:
            if script.name == script_name:
                script.enabled = True
                script.on_enable()
                return True
        return False

    def disable_script(self, script_name: str) -> bool:
        """Desabilita um script específico."""
        for script in self._scripts:
            if script.name == script_name:
                script.enabled = False
                script.on_disable()
                return True
        return False

    def execute_all(self, context: Dict[str, Any]) -> None:
        """Executa todos os scripts habilitados."""
        for script in self._scripts:
            if not script.enabled:
                continue

            try:
                executed = script.execute(context)
                if executed:
                    # Se script executou ação, pode querer pausar outros
                    # (exemplo: healing tem prioridade sobre attack)
                    pass
            except Exception as e:
                self._log.error(f"Erro no script '{script.name}': {e}", exc_info=True)

    def get_script(self, name: str) -> BaseScript | None:
        """Retorna script pelo nome."""
        for script in self._scripts:
            if script.name == name:
                return script
        return None

    def list_scripts(self) -> List[Dict[str, Any]]:
        """Lista todos os scripts registrados."""
        return [
            {
                "name": s.name,
                "enabled": s.enabled,
                "priority": s.priority,
            }
            for s in self._scripts
        ]
