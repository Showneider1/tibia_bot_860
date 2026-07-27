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

        # Dados do player - estaticos ate o bot_engine real ser integrado.
        # Nao ha simulacao aleatoria: os valores so mudam via update_from_engine().
        self._player_data = {
            "name": "--",
            "level": 0,
            "vocation": "--",
            "hp": 0,      "hp_max": 1,
            "mana": 0,    "mana_max": 1,
            "x": 0, "y": 0, "z": 0,
            "stamina": 0,
            "capacity": 0,
        }

        self._build_ui()
        self._bind_events()

    # ------------------------------------------------------------------
    # Integracao com o bot_engine real
    # ------------------------------------------------------------------
    def update_from_engine(self, player):
        """
        Chamado pelo BotEngine a cada tick quando um Player valido
        for lido da memoria. Atualiza a UI com dados reais.
        
        Uso no bot_engine.py:
            if self.player and hasattr(self, '_ui') and self._ui:
                self._ui.update_from_engine(self.player)
        """
        if player is None:
            return
        s = player.stats
        p = player.position
        self._player_data.update({
            "name":     player.name,
            "level":    player.level,
            "vocation": player.vocation,
            "hp":       s.health,
            "hp_max":   s.max_health,
            "mana":     s.mana,
            "mana_max": s.max_mana,
            "x":        p.x,
            "y":        p.y,
            "z":        p.z,
            "stamina":  player.stamina,
            "capacity": player.capacity,
        })
        # Agenda refresh na thread da UI (thread-safe)
        self.root.after(0, self._tabs["status"].refresh)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
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
        color  = COLORS["online_green"] if self.bot_running else COLORS["warn_yellow"]
        self.sidebar.update_bot_status(self.bot_running)
        self.log_panel.log(f"Bot {status}", color)

        if self.bot_running:
            self._connect_engine()

    def _connect_engine(self):
        """
        Tenta conectar ao BotEngine real.
        Se nao houver engine injetado, loga aviso - sem simulacao falsa.
        """
        if self.bot_engine is not None:
            ok = self.bot_engine.start()
            if ok:
                self.log_panel.log("Conectado ao Tibia. Lendo memoria...", COLORS["online_green"])
                self._start_engine_loop()
            else:
                self.log_panel.log("Falha ao conectar. Tibia esta aberto?", COLORS["warn_yellow"])
                self.bot_running = False
                self.sidebar.update_bot_status(False)
        else:
            self.log_panel.log(
                "[DEMO] Sem conexao com o jogo. Inicie via bot_engine para dados reais.",
                COLORS["text_faint"],
            )

    def _start_engine_loop(self):
        """Loop de leitura de memoria em thread separada."""
        def _loop():
            while self.bot_running and self.bot_engine:
                self.bot_engine.tick()
                player = self.bot_engine.player
                if player:
                    self.update_from_engine(player)
                time.sleep(0.15)
        threading.Thread(target=_loop, daemon=True).start()

    def log(self, msg: str, color: str = None):
        self.log_panel.log(msg, color)

    def _on_close(self):
        self.bot_running = False
        self.root.destroy()

    def run(self):
        self.log_panel.log(
            "TibiaBot 860 iniciado. Clique em INICIAR BOT para conectar.",
            COLORS["text_muted"],
        )
        self._tabs["status"].refresh()
        self.root.mainloop()
