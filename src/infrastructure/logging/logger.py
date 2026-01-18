"""
Logging centralizado do bot.
"""
import logging
import logging.handlers
from pathlib import Path

_LOGGER_CONFIGURED = False


def setup_logging(level: str = "INFO", log_file: str | None = None) -> None:
    """
    Configura logging global.

    Args:
        level: Nível mínimo (DEBUG, INFO, WARNING, ERROR)
        log_file: Caminho do arquivo de log (opcional)
    """
    global _LOGGER_CONFIGURED

    if _LOGGER_CONFIGURED:
        return

    # Converte string para nível numérico
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Cria pasta de logs se necessário
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Formato básico
    fmt = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers: list[logging.Handler] = []

    # Console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(logging.Formatter(fmt, datefmt))
    handlers.append(console_handler)

    # Arquivo (opcional)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(logging.Formatter(fmt, datefmt))
        handlers.append(file_handler)

    logging.basicConfig(
        level=numeric_level,
        handlers=handlers,
        force=True,
    )

    _LOGGER_CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger com nome padronizado.
    """
    return logging.getLogger(name)
