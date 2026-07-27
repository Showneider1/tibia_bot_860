"""
Aba de Healing - configuracao de auto-heal e auto-mana.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class HealingTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build()

    def _build(self):
        ctk.CTkLabel(self, text="Healing", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(self, text="Configure cura automatica de HP e Mana",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        self._hp_card(row=2, col=0)
        self._mana_card(row=2, col=1)
        self._spell_card(row=3)

    def _hp_card(self, row, col):
        card = self._card(row, col, "AUTO-HEAL (HP)")
        card.grid_columnconfigure(1, weight=1)

        enabled = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(card, text="Ativo", variable=enabled,
                      font=FONTS["body"],
                      text_color=COLORS["text_label"],
                      progress_color=COLORS["hp_red"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(6, 12), sticky="w")

        for i, (lbl, val, key) in enumerate([
            ("Usar abaixo de (%)", "60", "hp_pct"),
            ("Spell / Item",       "exura", "hp_spell"),
            ("Hotkey",             "F1", "hp_key"),
            ("Delay (ms)",         "300", "hp_delay"),
        ]):
            ctk.CTkLabel(card, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=2 + i, column=0, padx=(16, 8), pady=5, sticky="w")
            ctk.CTkEntry(card, placeholder_text=val, height=32, corner_radius=8,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"],
                         font=FONTS["body"]).grid(
                row=2 + i, column=1, padx=(0, 16), pady=5, sticky="ew")

    def _mana_card(self, row, col):
        card = self._card(row, col, "AUTO-MANA")
        card.grid_columnconfigure(1, weight=1)

        enabled = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(card, text="Ativo", variable=enabled,
                      font=FONTS["body"],
                      text_color=COLORS["text_label"],
                      progress_color=COLORS["mana_blue"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(6, 12), sticky="w")

        for i, (lbl, val) in enumerate([
            ("Usar abaixo de (%)", "40"),
            ("Spell / Item",       "exura gran"),
            ("Hotkey",             "F2"),
            ("Delay (ms)",         "400"),
        ]):
            ctk.CTkLabel(card, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=2 + i, column=0, padx=(16, 8), pady=5, sticky="w")
            ctk.CTkEntry(card, placeholder_text=val, height=32, corner_radius=8,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"],
                         font=FONTS["body"]).grid(
                row=2 + i, column=1, padx=(0, 16), pady=5, sticky="ew")

    def _spell_card(self, row):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=0, columnspan=2, padx=24, pady=(8, 24), sticky="nsew")
        card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(card, text="SPELLS DE EMERGENCIA",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=3, padx=16, pady=(14, 10), sticky="w")

        for col, (lbl, spell, pct, key) in enumerate([
            ("Critico HP", "exura vita", "20", "F3"),
            ("Critico Mana", "exura gran mas", "15", "F4"),
            ("Ult. Recurso", "exura sio", "10", "F5"),
        ]):
            ctk.CTkLabel(card, text=lbl, font=FONTS["subhead"],
                         text_color=COLORS["text_label"]).grid(row=1, column=col, padx=16, pady=4)
            ctk.CTkEntry(card, placeholder_text=spell, height=32, corner_radius=8,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"],
                         font=FONTS["body"]).grid(row=2, column=col, padx=12, pady=4, sticky="ew")
            ctk.CTkEntry(card, placeholder_text=f"Abaixo {pct}%", height=32, corner_radius=8,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"],
                         font=FONTS["body"]).grid(row=3, column=col, padx=12, pady=4, sticky="ew")

    def _card(self, row, col, title):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col,
                  padx=(24 if col == 0 else 8, 8 if col == 0 else 24),
                  pady=(0, 8), sticky="nsew")
        ctk.CTkLabel(card, text=title, font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 4), sticky="w")
        return card
