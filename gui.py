"""
Entry point da interface grafica do TibiaBot 860.
Uso: python gui.py
"""
import sys
import os

# Garante que src/ esta no path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.app import BotApp

if __name__ == "__main__":
    app = BotApp()
    app.run()
