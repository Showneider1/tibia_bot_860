"""
Pacote de scripts do BotEngine.

Cada script herda de BaseScript e é registrado no ScriptEngine.
Ordem de execução respeita `priority` (maior primeiro):
    - HealingScript : 100
    - BuffScript    : 90
    - AimbotScript  : 50
    - CavebotScript : 30
    - LooterScript  : 20
"""
from src.application.scripts.base_script import BaseScript
from src.application.scripts.script_engine import ScriptEngine
from src.application.scripts.healing_script import HealingScript
from src.application.scripts.buff_script import BuffScript
from src.application.scripts.aimbot_script import AimbotScript
from src.application.scripts.cavebot_script import CavebotScript
from src.application.scripts.looter_script import LooterScript

__all__ = [
    "BaseScript",
    "ScriptEngine",
    "HealingScript",
    "BuffScript",
    "AimbotScript",
    "CavebotScript",
    "LooterScript",
]
