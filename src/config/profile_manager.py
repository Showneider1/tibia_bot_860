"""
ProfileManager — F1.3

Persiste e carrega configuracoes de scripts por personagem em:
  settings/profiles/<nick_sanitizado>.yaml

Schema YAML:
  character: "Pall Knight"
  vocation: "Royal Paladin"
  scripts:
    healing:
      enabled: true
      hp_threshold: 60
      ...
    aimbot:
      enabled: false
      targeting_mode: "highest_xp"
      ...
    cavebot:
      enabled: false
      sections: []
    looter:
      enabled: false
      items_to_loot: {}
    buff:
      enabled: false
      enabled_buffs: []

Uso:
    pm = ProfileManager()
    pm.load("Pall Knight", script_engine)   # ao PLAYER_LOADED
    pm.save("Pall Knight", script_engine)   # manual ou via debounce
    pm.schedule_save("Pall Knight", script_engine)  # debounce 2s
"""
import re
import threading
import yaml
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from src.infrastructure.logging.logger import get_logger

if TYPE_CHECKING:
    from src.application.scripts.script_engine import ScriptEngine

# Mapa: nome interno do script -> chave YAML
_SCRIPT_KEY_MAP = {
    "HealingBot":   "healing",
    "BuffManager":  "buff",
    "AimBot":       "aimbot",
    "CaveBot":      "cavebot",
    "Looter":       "looter",
}

_PROFILES_DIR = Path("settings") / "profiles"


def _sanitize_name(name: str) -> str:
    """Remove caracteres invalidos para nomes de arquivo."""
    return re.sub(r"[^\w\-. ]", "_", name).strip().replace(" ", "_")


class ProfileManager:
    """Gerenciador de perfis por personagem (YAML)."""

    def __init__(self, profiles_dir: Optional[Path] = None):
        self._dir = Path(profiles_dir) if profiles_dir else _PROFILES_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._log = get_logger("ProfileManager")
        self._debounce_timer: Optional[threading.Timer] = None
        self._debounce_lock = threading.Lock()

    # ------------------------------------------------------------------
    # API publica
    # ------------------------------------------------------------------

    def load(self, character_name: str, script_engine: "ScriptEngine") -> None:
        """
        Carrega o perfil do personagem e aplica as configs nos scripts.
        Se o arquivo nao existir, cria o perfil default a partir do
        estado atual dos scripts (sem sobrescrever nada).
        """
        path = self._profile_path(character_name)
        if not path.exists():
            self._log.info(
                f"Perfil de '{character_name}' nao encontrado. "
                f"Criando em {path}."
            )
            self.save(character_name, script_engine)
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except Exception as e:
            self._log.error(f"Erro ao ler perfil '{path}': {e}")
            return

        scripts_data: dict = data.get("scripts", {})
        for internal_name, yaml_key in _SCRIPT_KEY_MAP.items():
            script = script_engine.get_script(internal_name)
            if script is None:
                continue
            cfg = scripts_data.get(yaml_key)
            if not isinstance(cfg, dict):
                continue

            # Aplica enabled separadamente (atributo de instancia)
            if "enabled" in cfg:
                script.enabled = bool(cfg["enabled"])

            # Aplica o restante em script.config
            for k, v in cfg.items():
                if k != "enabled":
                    script.config[k] = v

        self._log.info(f"Perfil de '{character_name}' carregado de {path}.")

    def save(self, character_name: str, script_engine: "ScriptEngine") -> None:
        """
        Serializa o estado atual de todos os scripts no YAML do personagem.
        Thread-safe.
        """
        path = self._profile_path(character_name)
        scripts_data = {}

        for internal_name, yaml_key in _SCRIPT_KEY_MAP.items():
            script = script_engine.get_script(internal_name)
            if script is None:
                scripts_data[yaml_key] = {"enabled": False}
                continue
            entry = {"enabled": script.enabled}
            for k, v in script.config.items():
                if k != "enabled":
                    entry[k] = v
            scripts_data[yaml_key] = entry

        data = {
            "character": character_name,
            "scripts": scripts_data,
        }

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
            self._log.info(f"Perfil de '{character_name}' salvo em {path}.")
        except Exception as e:
            self._log.error(f"Erro ao salvar perfil '{path}': {e}")

    def schedule_save(
        self,
        character_name: str,
        script_engine: "ScriptEngine",
        delay: float = 2.0,
    ) -> None:
        """
        Agenda um save com debounce de `delay` segundos.
        Chamadas repetidas dentro da janela reiniciam o timer
        (apenas um save efetivo ao final da rajada de mudancas).
        """
        with self._debounce_lock:
            if self._debounce_timer is not None:
                self._debounce_timer.cancel()
            self._debounce_timer = threading.Timer(
                delay,
                self._debounced_save,
                args=(character_name, script_engine),
            )
            self._debounce_timer.daemon = True
            self._debounce_timer.start()

    # ------------------------------------------------------------------
    # Internos
    # ------------------------------------------------------------------

    def _debounced_save(
        self, character_name: str, script_engine: "ScriptEngine"
    ) -> None:
        with self._debounce_lock:
            self._debounce_timer = None
        self.save(character_name, script_engine)

    def _profile_path(self, character_name: str) -> Path:
        return self._dir / f"{_sanitize_name(character_name)}.yaml"
