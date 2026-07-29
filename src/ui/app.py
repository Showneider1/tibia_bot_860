import threading
import time
import customtkinter as ctk

from src.ui.theme import COLORS, FONTS
from src.ui.widgets.sidebar import Sidebar
from src.ui.tabs.status_tab import StatusTab
from src.ui.tabs.healing_tab import HealingTab
from src.ui.tabs.aimbot_tab import AimbotTab
from src.ui.tabs.cavebot_tab import CavebotTab
from src.ui.tabs.settings_tab import SettingsTab
from src.ui.tabs.looter_tab import LooterTab
from src.ui.tabs.persistent_tab import PersistentTab
from src.ui.widgets.log_panel import LogPanel
from src.application.scripts.healing_script import HealingScript
from src.application.scripts.buff_script import BuffScript
from src.application.scripts.aimbot_script import AimbotScript
from src.application.scripts.cavebot_script import CavebotScript
from src.application.scripts.looter_script import LooterScript
from src.application.scripts.persistent_script import PersistentScript


class BotApp:
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.root = ctk.CTk()
        self.root.title("TibiaBot 860")
        self.root.geometry("1100x680")
        self.root.minsize(860, 560)
        self.root.configure(fg_color=COLORS["bg_dark"])

        self.bot_running = False
        self.bot_engine = None

        self._player_data = {
            "name":     "--",
            "level":    0,
            "vocation": "--",
            "hp":       0,  "hp_max":   1,
            "mana":     0,  "mana_max": 1,
            "x": 0, "y": 0, "z": 0,
            "stamina":  0,
            "capacity": 0,
        }

        self._build_ui()
        self._bind_events()

    def set_bot_engine(self, engine) -> None:
        self.bot_engine = engine
        self._register_default_scripts()

    def _register_default_scripts(self) -> None:
        if self.bot_engine is None:
            return
        se = self.bot_engine.script_engine
        registered = {s["name"] for s in se.list_scripts()}

        builtins = [
            ("HealingBot", HealingScript),
            ("BuffManager", BuffScript),
            ("AimBot",      AimbotScript),
            ("CaveBot",     CavebotScript),
            ("Looter",      LooterScript),
            ("Persistent",  PersistentScript),
        ]
        for name, script_cls in builtins:
            if name not in registered:
                script = script_cls()
                script.enabled = False
                se.register(script)

    def update_from_engine(self, player) -> None:
        if player is None:
            return

        try:
            s = player.stats
            p = player.position
            self._player_data.update({
                "name":     getattr(player, "name", "--") or "--",
                "level":    getattr(player, "level", 0) or 0,
                "vocation": getattr(player, "vocation", "--") or "--",
                "hp":       max(0, min(s.health, s.max_health)),
                "hp_max":   max(1, s.max_health),
                "mana":     max(0, min(s.mana, s.max_mana)),
                "mana_max": max(1, s.max_mana),
                "x":        p.x,
                "y":        p.y,
                "z":        p.z,
                "stamina":  getattr(player, "stamina", 0) or 0,
                "capacity": getattr(player, "capacity", 0) or 0,
            })
        except Exception:
            return

        self.root.after(0, self._tabs["status"].refresh)

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        self.sidebar = Sidebar(self.root, self)
        self.sidebar.grid(row=0, column=0, sticky="nsew")

        self._content = ctk.CTkFrame(
            self.root, fg_color=COLORS["bg_dark"], corner_radius=0
        )
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

        self._tabs = {
            "status":     StatusTab(self._content, self),
            "healing":    HealingTab(self._content, self),
            "aimbot":     AimbotTab(self._content, self),
            "cavebot":    CavebotTab(self._content, self),
            "looter":     LooterTab(self._content, self),
            "persistent": PersistentTab(self._content, self),
            "settings":   SettingsTab(self._content, self),
        }
        for tab in self._tabs.values():
            tab.grid(row=0, column=0, sticky="nsew")

        self.log_panel = LogPanel(self.root)
        self.log_panel.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.show_tab("status")

    def _bind_events(self) -> None:
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def show_tab(self, name: str) -> None:
        for key, tab in self._tabs.items():
            if key == name:
                tab.tkraise()
        self.sidebar.set_active(name)

    def toggle_bot(self) -> None:
        self.bot_running = not self.bot_running
        status = "ATIVADO" if self.bot_running else "PAUSADO"
        color  = COLORS["online_green"] if self.bot_running else COLORS["warn_yellow"]
        self.sidebar.update_bot_status(self.bot_running)
        self.log_panel.log(f"Bot {status}", color)

        if self.bot_running:
            self._connect_engine()
        else:
            if self.bot_engine:
                self.bot_engine.enabled = False

    def _connect_engine(self) -> None:
        if self.bot_engine is None:
            self.log_panel.log(
                "[DEMO] Sem BotEngine injetado.",
                COLORS["text_faint"],
            )
            return

        ok = self.bot_engine.start()
        if ok:
            self.bot_engine.enabled = True
            self.log_panel.log("Conectado ao Tibia.", COLORS["online_green"])
            self._start_engine_loop()
        else:
            self.log_panel.log("Falha ao conectar.", COLORS["warn_yellow"])
            self.bot_running = False
            self.sidebar.update_bot_status(False)

    def _start_engine_loop(self) -> None:
        engine = self.bot_engine

        def _loop():
            while self.bot_running and engine:
                try:
                    engine.tick()
                    if engine.player:
                        self.update_from_engine(engine.player)
                except Exception as exc:
                    self.root.after(
                        0,
                        lambda e=exc: self.log_panel.log(
                            f"Erro: {e}", COLORS["warn_yellow"]
                        ),
                    )
                time.sleep(0.15)

        threading.Thread(target=_loop, daemon=True, name="BotEngineLoop").start()

    def log(self, msg: str, color: str = None) -> None:
        self.log_panel.log(msg, color)

    def _on_close(self) -> None:
        self.bot_running = False
        if self.bot_engine:
            self.bot_engine.stop()
        self.root.destroy()

    def run(self) -> None:
        self.log_panel.log(
            "TibiaBot 860 iniciado.",
            COLORS["text_muted"],
        )
        self._tabs["status"].refresh()
        self.root.mainloop()
