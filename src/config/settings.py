"""
Gerenciador de configurações.
"""
import yaml
from pathlib import Path
from typing import Any, Dict
from src.infrastructure.logging.logger import get_logger


class Settings:
    """Gerenciador de configurações do bot."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._log = get_logger("Settings")
        self.load()
    
    def load(self) -> None:
        """Carrega configurações do arquivo."""
        if not self.config_path.exists():
            self._log.warning(f"Arquivo de config não encontrado: {self.config_path}")
            self._create_default()
            return
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
            self._log.info(f"Configurações carregadas de {self.config_path}")
        except Exception as e:
            self._log.error(f"Erro ao carregar config: {e}")
            self._config = {}
    
    def save(self) -> None:
        """Salva configurações no arquivo."""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(self._config, f, default_flow_style=False)
            self._log.info(f"Configurações salvas em {self.config_path}")
        except Exception as e:
            self._log.error(f"Erro ao salvar config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtém valor da configuração.
        Suporta notação de ponto: "scripts.healing.enabled"
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """
        Define valor na configuração.
        Suporta notação de ponto: "scripts.healing.enabled"
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def _create_default(self) -> None:
        """Cria configuração padrão."""
        self._config = {
            "bot": {
                "name": "TibiaBot860",
                "version": "1.0.0"
            },
            "player": {
                "vocation": "Auto"
            },
            "logging": {
                "level": "INFO",
                "file": "logs/bot.log",
                "console": True
            },
            "scripts": {
                "healing": {"enabled": False},
                "aimbot": {"enabled": False},
                "cavebot": {"enabled": False},
                "looter": {"enabled": False}
            }
        }
        self.save()
