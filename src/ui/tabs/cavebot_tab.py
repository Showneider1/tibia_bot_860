"""
Aba de Cavebot - waypoints e configuracoes de hunt.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


SAMPLE_WAYPOINTS = [
    ("1", "32337", "31786", "7", "Walk"),
    ("2", "32340", "31790", "7", "Walk"),
    ("3", "32350", "31800", "7", "Attack"),
    ("4", "32345", "31805", "7", "Loot"),
]


class CavebotTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Cavebot", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(self, text="Gerencie waypoints e comportamento do bot em cave",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        self._waypoint_panel()
        self._config_panel()

    def _waypoint_panel(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=0, padx=(24, 8), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(2, weight=1)

        # Header
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="WAYPOINTS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        for txt, color in [("+ Adicionar", COLORS["accent"]), ("Limpar", COLORS["hp_red"])]:
            ctk.CTkButton(btn_frame, text=txt, font=FONTS["small"], height=28,
                          corner_radius=8, fg_color=color,
                          hover_color=COLORS["accent_hover"]).pack(side="left", padx=4)

        # Cabecalho da tabela
        headers = ["#", "X", "Y", "Z", "Acao"]
        widths = [30, 70, 70, 40, 80]
        col_frame = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=6)
        col_frame.grid(row=1, column=0, padx=12, pady=(0, 4), sticky="ew")
        for j, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(col_frame, text=h, font=FONTS["badge"],
                         text_color=COLORS["text_faint"], width=w).pack(side="left", padx=6, pady=6)

        # Scroll de waypoints
        scroll = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        scroll.grid(row=2, column=0, padx=12, pady=(0, 12), sticky="nsew")

        for wp in SAMPLE_WAYPOINTS:
            row = ctk.CTkFrame(scroll, fg_color=COLORS["bg_panel"], corner_radius=8)
            row.pack(fill="x", pady=3)
            for j, (val, w) in enumerate(zip(wp, widths)):
                color = COLORS["text_muted"] if j > 0 else COLORS["accent_light"]
                ctk.CTkLabel(row, text=val, font=FONTS["body"],
                             text_color=color, width=w).pack(side="left", padx=6, pady=8)

    def _config_panel(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=1, padx=(0, 24), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="OPCOES", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        for i, (lbl, default) in enumerate([
            ("Lootar criaturas",    True),
            ("Atacar automatico",   True),
            ("Usar escalada",       False),
            ("Pausar se atacado",   False),
            ("Voltar ao start",     True),
        ]):
            var = ctk.BooleanVar(value=default)
            ctk.CTkSwitch(card, text=lbl, variable=var,
                          font=FONTS["body"],
                          text_color=COLORS["text_label"],
                          progress_color=COLORS["accent"]).grid(
                row=i + 1, column=0, padx=16, pady=6, sticky="w")

        ctk.CTkLabel(card, text="Modo de alvo", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=10, column=0, padx=16, pady=(16, 4), sticky="w")
        ctk.CTkComboBox(card,
                        values=["Menor HP", "Mais proximo", "Mais longe", "Mais forte"],
                        font=FONTS["body"],
                        fg_color=COLORS["bg_input"],
                        border_color=COLORS["border"],
                        text_color=COLORS["text_label"],
                        button_color=COLORS["accent"],
                        dropdown_fg_color=COLORS["bg_card"]).grid(
            row=11, column=0, padx=16, pady=(0, 16), sticky="ew")
