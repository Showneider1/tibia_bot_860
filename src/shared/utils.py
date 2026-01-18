import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    """Carrega JSON de arquivo."""
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Salva JSON em arquivo."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
