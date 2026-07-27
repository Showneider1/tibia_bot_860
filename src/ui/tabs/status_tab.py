"""
Aba de Status - exibe dados do player em tempo real.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class StatusTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        # Titulo
        title = ctk.CTkLabel(self, text="Status do Personagem", font=FONTS["title"],
                             text_color=COLORS["text_primary"])
        title.grid(row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        sub = ctk.CTkLabel(self, text="Dados lidos em tempo real da memoria do jogo",
                           font=FONTS["small"], text_color=COLORS["text_faint"])
        sub.grid(row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        # Card esquerdo: identidade
        self._id_card = self._make_card(row=2, col=0)
        # Card direito: stats
        self._stats_card = self._make_card(row=2, col=1)

    def _make_card(self, row, col):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col, padx=(24 if col == 0 else 8, 8 if col == 0 else 24),
                  pady=(0, 24), sticky="nsew")
        return card

    def refresh(self):
        p = self.app._mock_player
        self._build_id_card(p)
        self._build_stats_card(p)

    def _build_id_card(self, p):
        for w in self._id_card.winfo_children():
            w.destroy()
        self._id_card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self._id_card, text="IDENTIDADE",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 10), sticky="w")

        rows = [
            ("Nome",     p["name"]),
            ("Nivel",    str(p["level"])),
            ("Vocacao",  p["vocation"]),
            ("Stamina",  f"{p['stamina'] // 60}h {p['stamina'] % 60}m"),
            ("Capacidade", f"{p['capacity'] // 100:.0f} oz"),
            ("Posicao",  f"X:{p['x']}  Y:{p['y']}  Z:{p['z']}"),
        ]
        for i, (lbl, val) in enumerate(rows):
            ctk.CTkLabel(self._id_card, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=i + 1, column=0, padx=(16, 8), pady=4, sticky="w")
            ctk.CTkLabel(self._id_card, text=val, font=FONTS["body"],
                         text_color=COLORS["text_label"]).grid(
                row=i + 1, column=1, padx=(0, 16), pady=4, sticky="w")

    def _build_stats_card(self, p):
        for w in self._stats_card.winfo_children():
            w.destroy()
        self._stats_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._stats_card, text="VIDA & MANA",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=16, pady=(14, 10), sticky="w")

        hp_pct = p["hp"] / max(p["hp_max"], 1)
        mana_pct = p["mana"] / max(p["mana_max"], 1)

        self._bar(self._stats_card, 1, "HP", p["hp"], p["hp_max"],
                  hp_pct, COLORS["hp_red"], COLORS["hp_bg"])
        self._bar(self._stats_card, 2, "Mana", p["mana"], p["mana_max"],
                  mana_pct, COLORS["mana_blue"], COLORS["mana_bg"])

        # Valores grandes
        vals = ctk.CTkFrame(self._stats_card, fg_color="transparent")
        vals.grid(row=3, column=0, padx=16, pady=12, sticky="ew")
        vals.grid_columnconfigure((0, 1), weight=1)

        for col, (lbl, val, color) in enumerate([
            ("HP",   f"{p['hp']}/{p['hp_max']}",     COLORS["hp_red"]),
            ("Mana", f"{p['mana']}/{p['mana_max']}", COLORS["mana_blue"]),
        ]):
            ctk.CTkLabel(vals, text=val, font=FONTS["stat_val"],
                         text_color=color).grid(row=0, column=col, padx=8)
            ctk.CTkLabel(vals, text=lbl, font=FONTS["stat_lbl"],
                         text_color=COLORS["text_faint"]).grid(row=1, column=col, padx=8)

    def _bar(self, parent, row, label, val, max_val, pct, color, bg):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.grid(row=row, column=0, padx=16, pady=(6, 0), sticky="ew")
        row_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(row_frame, text=label, font=FONTS["small"],
                     text_color=COLORS["text_faint"], width=36).grid(row=0, column=0, sticky="w")
        bar = ctk.CTkProgressBar(row_frame, height=12, corner_radius=6,
                                  fg_color=bg, progress_color=color)
        bar.set(pct)
        bar.grid(row=0, column=1, padx=(8, 0), sticky="ew")
