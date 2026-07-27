"""
Janela principal do TibiaBot 860 UI.
"""
import threading
import time
import customtkinter as ctk

from src.ui.theme import COLORS, FONTS
from src.ui.widgets.sidebar import Sidebar
from src.ui.tabs.status_tab import StatusTab
from src.ui.tabs.healing_tab import HealingTab
from src.ui.tabs.cavebot_tab import CavebotTab
from src.ui.tabs.settings_tab import SettingsTab
from src.ui.widgets.log_panel import LogPanel


class BotApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("TibiaBot 860")
        self.root.geometry("1140x740")
        self.root.minsize(900, 620)
        self.root.configure(fg_color=COLORS["bg_dark"])

        self.bot_running = False
        self.bot_engine = None

        # Mock — valores SEMPRE respeitam o maximo
        self._mock_player = {
            "name": "Specter Um",
            "level": 109,
            "vocation": "Elder Druid",
            "hp": 690, "hp_max": 690,
            "mana": 2985, "mana_max": 3065,
            "x": 32337, "y": 31790, "z": 7,
            "stamina": 2520,
            "capacity": 76450,
        }

        self._build_ui()
        self._bind_events()

    def _build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self.root, self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self._content = ctk.CTkFrame(self.root, fg_color=COLORS["bg_dark"], corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._tabs = {
            "status":   StatusTab(self._content, self),
            "healing":  HealingTab(self._content, self),
            "cavebot":  CavebotTab(self._content, self),
            "settings": SettingsTab(self._content, self),
        }
        for tab in self._tabs.values():
            tab.grid(row=0, column=0, sticky="nsew")

        self.log_panel = LogPanel(self.root)
        self.log_panel.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.show_tab("status")

    def _bind_events(self):
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_tab(self, name: str):
        for key, tab in self._tabs.items():
            if key == name:
                tab.tkraise()
        self.sidebar.set_active(name)

    def toggle_bot(self):
        self.bot_running = not self.bot_running
        status = "ATIVADO" if self.bot_running else "PAUSADO"
        color = COLORS["online_green"] if self.bot_running else COLORS["warn_yellow"]
        self.sidebar.update_bot_status(self.bot_running)
        self.log_panel.log(f"Bot {status}", color)
        if self.bot_running:
            self._start_mock_updates()

    def _start_mock_updates(self):
        """Simula variacoes de HP/Mana dentro dos limites corretos."""
        def _loop():
            import random
            while self.bot_running:
                p = self._mock_player
                # Clamp: nunca ultrapassa o maximo nem vai abaixo de 1
                p["hp"]   = max(1, min(p["hp_max"],   p["hp"]   + random.randint(-20, 15)))
                p["mana"] = max(1, min(p["mana_max"], p["mana"] + random.randint(-30, 20)))
                self.root.after(0, self._tabs["status"].refresh)
                time.sleep(1.5)
        threading.Thread(target=_loop, daemon=True).start()

    def log(self, msg: str, color: str = None):
        self.log_panel.log(msg, color)

    def _on_close(self):
        self.bot_running = False
        self.root.destroy()

    def run(self):
        self.log_panel.log("TibiaBot 860 iniciado. Aguardando conexao com o jogo...", COLORS["text_muted"])
        self.root.mainloop()
