"""
Sidebar de navegacao lateral - versao refinada.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS

NAV_ITEMS = [
    ("status",   "\u26A1", "Status"),
    ("healing",  "\u2764", "Healing"),
    ("cavebot",  "\u2694", "Cavebot"),
    ("settings", "\u2699", "Config"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_sidebar"], corner_radius=0, width=190)
        self.app = app
        self._buttons = {}
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_rowconfigure(9, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Logo
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=18, pady=(26, 0), sticky="w")
        ctk.CTkLabel(logo_frame, text="\u2620", font=("Segoe UI", 22),
                     text_color=COLORS["accent"]).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(logo_frame, text="TibiaBot", font=("Segoe UI", 17, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")

        ctk.CTkLabel(self, text="v1.0  \u2022  8.60",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, padx=20, pady=(2, 18), sticky="w")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).grid(
            row=2, column=0, sticky="ew", padx=14, pady=(0, 14))

        # Navegacao
        for i, (key, icon, label) in enumerate(NAV_ITEMS):
            btn = ctk.CTkButton(
                self,
                text=f"  {icon}   {label}",
                font=("Segoe UI", 12, "bold"),
                anchor="w",
                height=46,
                corner_radius=12,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_hover"],
                command=lambda k=key: self.app.show_tab(k),
            )
            btn.grid(row=3 + i, column=0, padx=10, pady=2, sticky="ew")
            self._buttons[key] = btn

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent").grid(row=9, column=0, sticky="nsew")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).grid(
            row=10, column=0, sticky="ew", padx=14, pady=(0, 10))

        # Status indicator
        self._status_row = ctk.CTkFrame(self, fg_color="transparent")
        self._status_row.grid(row=11, column=0, padx=18, pady=(0, 8), sticky="w")
        self._dot = ctk.CTkLabel(self._status_row, text="\u25CF",
                                  font=("Segoe UI", 10), text_color=COLORS["offline_gray"])
        self._dot.pack(side="left", padx=(0, 6))
        self._status_lbl = ctk.CTkLabel(self._status_row, text="Offline",
                                         font=FONTS["small"], text_color=COLORS["text_faint"])
        self._status_lbl.pack(side="left")

        # Botao START/STOP
        self._start_btn = ctk.CTkButton(
            self,
            text="  \u25B6   INICIAR BOT",
            font=("Segoe UI", 12, "bold"),
            height=46,
            corner_radius=12,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.app.toggle_bot,
        )
        self._start_btn.grid(row=12, column=0, padx=12, pady=(0, 24), sticky="ew")

    def update_bot_status(self, running: bool):
        if running:
            self._dot.configure(text_color=COLORS["online_green"])
            self._status_lbl.configure(text="Online", text_color=COLORS["online_green"])
            self._start_btn.configure(
                text="  \u23F9   PARAR BOT",
                fg_color="#c0392b",
                hover_color="#96281b",
            )
        else:
            self._dot.configure(text_color=COLORS["offline_gray"])
            self._status_lbl.configure(text="Offline", text_color=COLORS["text_faint"])
            self._start_btn.configure(
                text="  \u25B6   INICIAR BOT",
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
            )

    def set_active(self, key: str):
        for k, btn in self._buttons.items():
            if k == key:
                btn.configure(
                    fg_color=COLORS["bg_hover"],
                    text_color=COLORS["accent_light"],
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_muted"],
                )
