"""
Ponto de entrada da interface grafica do TibiaBot 860.

Uso:
    python gui.py
    python -m gui

Para integrar com o BotEngine:
    from src.application.bot_engine import BotEngine
    from src.ui.app import BotApp

    engine = BotEngine(...)  # configure seus componentes
    app = BotApp()
    app.bot_engine = engine  # injeta antes de run()
    app.run()
"""
import sys
import os

# Garante que o diretorio raiz esta no sys.path
sys.path.insert(0, os.path.dirname(__file__))

from src.ui.app import BotApp


def main():
    app = BotApp()
    app.run()


if __name__ == "__main__":
    main()
