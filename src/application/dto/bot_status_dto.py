from dataclasses import dataclass
from typing import Optional


@dataclass
class BotStatusDTO:
    """DTO de status geral do bot."""
    connected: bool
    running: bool
    enabled: bool
    action: str = "idle"
    target_name: Optional[str] = None
