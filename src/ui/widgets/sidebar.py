import customtkinter as ctk
from src.ui.theme import COLORS, FONTS

NAV_ITEMS = [
    ("status",     "\u26A1", "Status"),
    ("healing",    "\u2764", "Healing"),
    ("aimbot",     "\u26F9", "Aimbot"),
    ("cavebot",    "\u2694", "Cavebot"),
    ("looter",     "\U0001F4B0", "Looter"),
    ("persistent", "\U0001F4CB", "Persistent"),
    ("settings",   "\u2699", "Config"),
]


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_sidebar"], corner_radius=0, width=170)
        self.app = app
        self._buttons = {}
        self._indicators = {}
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_rowconfigure(10, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.grid(row=0, column=0, columnspan=2, padx=14, pady=(18, 0), sticky="w")
        ctk.CTkLabel(logo_frame, text="\u2620", font=("Segoe UI", 18),
                     text_color=COLORS["accent"]).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(logo_frame, text="TibiaBot", font=("Segoe UI", 15, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")

        ctk.CTkLabel(self, text="v1.0 \u2022 8.60",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(1, 12), sticky="w")

        sep_frame = ctk.CTkFrame(self, fg_color="transparent")
        sep_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 8))
        ctk.CTkFrame(sep_frame, fg_color=COLORS["border"], height=1).pack(fill="x")

        for i, (key, icon, label) in enumerate(NAV_ITEMS):
            row = i + 3

            indicator = ctk.CTkFrame(self, fg_color=COLORS["bg_sidebar"], width=3, height=38)
            indicator.grid(row=row, column=0, sticky="ns")
            self._indicators[key] = indicator

            btn = ctk.CTkButton(
                self,
                text=f"  {icon}   {label}",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
                height=38,
                corner_radius=0,
                fg_color="transparent",
                text_color=COLORS["text_muted"],
                hover_color=COLORS["bg_hover"],
                command=lambda k=key: self.app.show_tab(k),
            )
            btn.grid(row=row, column=1, sticky="ew", padx=(0, 10))
            self._buttons[key] = btn

        ctk.CTkFrame(self, fg_color="transparent").grid(row=10, column=0, columnspan=2, sticky="nsew")

        sep_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        sep_frame2.grid(row=11, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 6))
        ctk.CTkFrame(sep_frame2, fg_color=COLORS["border"], height=1).pack(fill="x")

        self._status_row = ctk.CTkFrame(self, fg_color="transparent")
        self._status_row.grid(row=12, column=0, columnspan=2, padx=14, pady=(0, 4), sticky="w")
        self._dot = ctk.CTkLabel(self._status_row, text="\u25CF",
                                  font=("Segoe UI", 9), text_color=COLORS["offline_gray"])
        self._dot.pack(side="left", padx=(0, 5))
        self._status_lbl = ctk.CTkLabel(self._status_row, text="Offline",
                                         font=FONTS["small"], text_color=COLORS["text_faint"])
        self._status_lbl.pack(side="left")

        self._start_btn = ctk.CTkButton(
            self,
            text="  \u25B6   INICIAR BOT",
            font=("Segoe UI", 11, "bold"),
            height=38,
            corner_radius=8,
            fg_color=COLORS["accent_dim"],
            hover_color=COLORS["accent"],
            text_color=COLORS["accent_light"],
            command=self.app.toggle_bot,
        )
        self._start_btn.grid(row=13, column=0, columnspan=2, padx=10, pady=(0, 16), sticky="ew")

    def update_bot_status(self, running: bool):
        if running:
            self._dot.configure(text_color=COLORS["online_green"])
            self._status_lbl.configure(text="Online", text_color=COLORS["online_green"])
            self._start_btn.configure(
                text="  \u23F9   PARAR BOT",
                fg_color="#2a1018",
                hover_color="#4a1a28",
                text_color=COLORS["hp_red"],
            )
        else:
            self._dot.configure(text_color=COLORS["offline_gray"])
            self._status_lbl.configure(text="Offline", text_color=COLORS["text_faint"])
            self._start_btn.configure(
                text="  \u25B6   INICIAR BOT",
                fg_color=COLORS["accent_dim"],
                hover_color=COLORS["accent"],
                text_color=COLORS["accent_light"],
            )

    def set_active(self, key: str):
        for k, btn in self._buttons.items():
            indicator = self._indicators[k]
            if k == key:
                indicator.configure(fg_color=COLORS["accent"])
                btn.configure(
                    fg_color=COLORS["bg_active"],
                    text_color=COLORS["accent_light"],
                )
            else:
                indicator.configure(fg_color=COLORS["bg_sidebar"])
                btn.configure(
                    fg_color="transparent",
                    text_color=COLORS["text_muted"],
                )
