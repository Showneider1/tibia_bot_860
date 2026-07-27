"""
Sidebar de navegacao lateral.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


NAV_ITEMS = [
    ("status",   "\u26a1",  "Status"),
    ("healing",  "\u2764",  "Healing"),
    ("cavebot",  "\u2694",  "Cavebot"),
    ("settings", "\u2699",  "Config"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_sidebar"], corner_radius=0, width=180)
        self.app = app
        self._active = "status"
        self._buttons = {}
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_rowconfigure(10, weight=1)

        # Logo
        logo = ctk.CTkLabel(
            self, text="\u2620  TibiaBot",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS["accent_light"],
            pady=0,
        )
        logo.grid(row=0, column=0, padx=20, pady=(24, 4), sticky="w")

        ver = ctk.CTkLabel(self, text="v1.0  |  8.60", font=FONTS["small"], text_color=COLORS["text_faint"])
        ver.grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        sep = ctk.CTkFrame(self, fg_color=COLORS["border"], height=1)
        sep.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 12))

        # Botoes de navegacao
        for i, (key, icon, label) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}  {label}",
                font=FONTS["nav"],
                anchor="w",
                height=44,
                corner_radius=10,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_hover"],
                command=lambda k=key: self.app.show_tab(k),
            )
            btn.grid(row=3 + i, column=0, padx=12, pady=3, sticky="ew")
            self._buttons[key] = btn

        sep2 = ctk.CTkFrame(self, fg_color=COLORS["border"], height=1)
        sep2.grid(row=10, column=0, sticky="ew", padx=16, pady=12)

        # Status dot + botao START/STOP
        self._status_dot = ctk.CTkLabel(self, text="\u25cf  Offline", font=FONTS["small"],
                                         text_color=COLORS["offline_gray"])
        self._status_dot.grid(row=11, column=0, padx=20, pady=(4, 4), sticky="w")

        self._start_btn = ctk.CTkButton(
            self,
            text="  \u25b6  INICIAR BOT",
            font=("Segoe UI", 12, "bold"),
            height=42,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._toggle,
        )
        self._start_btn.grid(row=12, column=0, padx=12, pady=(4, 24), sticky="ew")

    def _toggle(self):
        self.app.toggle_bot()

    def update_bot_status(self, running: bool):
        if running:
            self._status_dot.configure(text="\u25cf  Online", text_color=COLORS["online_green"])
            self._start_btn.configure(
                text="  \u23f9  PARAR BOT",
                fg_color=COLORS["hp_red"],
                hover_color="#c04040",
            )
        else:
            self._status_dot.configure(text="\u25cf  Offline", text_color=COLORS["offline_gray"])
            self._start_btn.configure(
                text="  \u25b6  INICIAR BOT",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
            )

    def set_active(self, key: str):
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(fg_color=COLORS["bg_hover"], text_color=COLORS["accent_light"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text_muted"])
        self._active = key
