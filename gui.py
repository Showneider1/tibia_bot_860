"""
Ponto de entrada da interface grafica do TibiaBot 860.

Uso:
    python gui.py              (abre a UI; bot conecta ao clicar INICIAR)
    python -m gui

Requisitos:
    - Windows
    - Executar como Administrador
    - Tibia 8.60 / Kaldrox aberto e logado
"""
import sys
import os
import ctypes
import logging

# Garante que o diretorio raiz esta no sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)


def _is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _build_engine():
    """
    Instancia e retorna um BotEngine pronto para ser injetado na BotApp.
    Retorna None se falhar (a UI abre em modo demo).
    """
    try:
        from src.infrastructure.memory.process_manager import ProcessManager
        from src.infrastructure.memory.memory_reader import MemoryReader
        from src.infrastructure.injection.keyboard_injector import KeyboardInjector
        from src.application.bot_engine import BotEngine
        from src.core.constants.addresses_860 import PLAYER, BATTLE_LIST, CREATURE, PLAYER_EXTRA
        from src.application.scripts.aimbot_script import AimbotScript
        from src.application.scripts.healing_script import HealingScript
        from src.application.scripts.buff_script import BuffScript
        from src.application.scripts.cavebot_script import CavebotScript

        pm = ProcessManager()
        mr = MemoryReader(pm)
        ki = KeyboardInjector()

        engine = BotEngine(
            process_manager=pm,
            memory_reader=mr,
            keyboard_injector=ki,
            player_addresses={**PLAYER, **PLAYER_EXTRA},
            battle_list_addresses=BATTLE_LIST,
            creature_offsets=CREATURE,
        )

        # BUG #1 FIX: registrar todos os scripts no ScriptEngine.
        # Antes apenas HealingScript/BuffScript/CavebotScript eram registrados
        # implicitamente; AimbotScript nunca era adicionado e portanto nunca
        # executava, fazendo o char nunca atacar.
        engine.script_engine.register(HealingScript())
        engine.script_engine.register(AimbotScript())
        engine.script_engine.register(BuffScript())
        engine.script_engine.register(CavebotScript())

        return engine
    except Exception as exc:
        logging.getLogger("gui").error(f"Falha ao criar BotEngine: {exc}", exc_info=True)
        return None


def main():
    from src.ui.app import BotApp
    from src.ui.theme import COLORS

    app = BotApp()

    if not _is_admin():
        # Avisa na UI mas nao trava -- usuario pode corrigir sem fechar
        app.log(
            "AVISO: Execute como Administrador para leitura de memoria funcionar.",
            COLORS.get("warn_yellow", "#f5a623"),
        )

    engine = _build_engine()
    if engine is not None:
        app.set_bot_engine(engine)
    else:
        app.log(
            "[DEMO] Falha ao criar BotEngine. Verifique os logs. Rodando em modo demo.",
            COLORS.get("warn_yellow", "#f5a623"),
        )

    app.run()


if __name__ == "__main__":
    main()
