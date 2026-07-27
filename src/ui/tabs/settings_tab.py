"""
Aba de Configuracoes gerais.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Configuracoes", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(self, text="Opcoes gerais do bot e conexao com o jogo",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        self._conn_card()
        self._pref_card()

    def _conn_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=0, padx=(24, 8), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="CONEXAO", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 10), sticky="w")

        for i, (lbl, val) in enumerate([
            ("Processo alvo",   "Not Open.exe"),
            ("Intervalo de tick (ms)", "100"),
            ("Timeout de reconexao (s)", "30"),
        ]):
            ctk.CTkLabel(card, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=i + 1, column=0, padx=(16, 8), pady=6, sticky="w")
            ctk.CTkEntry(card, placeholder_text=val, height=32, corner_radius=8,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"],
                         font=FONTS["body"]).grid(
                row=i + 1, column=1, padx=(0, 16), pady=6, sticky="ew")

        ctk.CTkButton(card, text="  Testar Conexao", font=FONTS["body"], height=36,
                      corner_radius=10, fg_color=COLORS["accent"],
                      hover_color=COLORS["accent_hover"]).grid(
            row=10, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="ew")

    def _pref_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=1, padx=(0, 24), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="PREFERENCIAS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        for i, (lbl, default) in enumerate([
            ("Iniciar bot ao abrir",   False),
            ("Minimizar na bandeja",   True),
            ("Som ao level up",        True),
            ("Logs detalhados (DEBUG)",False),
            ("Auto-reconnect",         True),
        ]):
            var = ctk.BooleanVar(value=default)
            ctk.CTkSwitch(card, text=lbl, variable=var,
                          font=FONTS["body"],
                          text_color=COLORS["text_label"],
                          progress_color=COLORS["accent"]).grid(
                row=i + 1, column=0, padx=16, pady=7, sticky="w")

        ctk.CTkLabel(card, text="Tema", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=10, column=0, padx=16, pady=(16, 4), sticky="w")
        ctk.CTkSegmentedButton(card,
                               values=["Dark", "Light", "Sistema"],
                               font=FONTS["body"],
                               fg_color=COLORS["bg_input"],
                               selected_color=COLORS["accent"],
                               selected_hover_color=COLORS["accent_hover"],
                               text_color=COLORS["text_label"]).grid(
            row=11, column=0, padx=16, pady=(0, 12), sticky="ew")

        ctk.CTkButton(card, text="  Salvar Configuracoes", font=FONTS["body"], height=36,
                      corner_radius=10, fg_color=COLORS["accent"],
                      hover_color=COLORS["accent_hover"]).grid(
            row=12, column=0, padx=16, pady=(4, 16), sticky="ew")
