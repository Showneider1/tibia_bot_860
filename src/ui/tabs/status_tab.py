"""
Aba de Status - redesenhada com layout mais refinado.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class StatusTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=28, pady=(22, 0), sticky="ew")
        ctk.CTkLabel(hdr, text="Status do Personagem", font=("Segoe UI", 22, "bold"),
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkLabel(hdr, text="Leitura em tempo real da memoria",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).pack(
            side="left", padx=(14, 0), pady=(6, 0))

        # Separador
        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=28, pady=(10, 0))

        # Conteudo principal
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, padx=28, pady=18, sticky="nsew")
        self.grid_rowconfigure(2, weight=1)
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure(0, weight=1)

        self._id_card = self._card(body, 0, 0, padx=(0, 10))
        self._vitals_card = self._card(body, 0, 1, padx=(10, 0))

    def _card(self, parent, row, col, padx=(0, 0)):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=16,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=col, padx=padx, pady=0, sticky="nsew")
        return card

    def refresh(self):
        p = self.app._mock_player
        self._draw_id(p)
        self._draw_vitals(p)

    # ------------------------------------------------------------------
    def _draw_id(self, p):
        for w in self._id_card.winfo_children():
            w.destroy()
        self._id_card.grid_columnconfigure(0, weight=1)

        # Titulo do card
        ctk.CTkLabel(self._id_card, text="IDENTIDADE",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=20, pady=(18, 6), sticky="w")
        ctk.CTkFrame(self._id_card, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=20, pady=(0, 12))

        # Nome em destaque
        ctk.CTkLabel(self._id_card, text=p["name"],
                     font=("Segoe UI", 18, "bold"),
                     text_color=COLORS["text_primary"]).grid(
            row=2, column=0, padx=20, pady=(0, 2), sticky="w")
        ctk.CTkLabel(self._id_card, text=p["vocation"],
                     font=FONTS["body"], text_color=COLORS["accent_light"]).grid(
            row=3, column=0, padx=20, pady=(0, 16), sticky="w")

        # Grade de atributos
        attrs = [
            ("\u2B50  Nivel",       str(p["level"])),
            ("\u23F1  Stamina",     f"{p['stamina'] // 60}h {p['stamina'] % 60:02d}m"),
            ("\U0001F4E6  Capacidade", f"{p['capacity'] / 100:.0f} oz"),
            ("\U0001F4CD  Posicao",   f"X {p['x']}   Y {p['y']}   Z {p['z']}"),
        ]
        for i, (lbl, val) in enumerate(attrs):
            row_bg = COLORS["bg_panel"] if i % 2 == 0 else "transparent"
            row_f = ctk.CTkFrame(self._id_card, fg_color=row_bg, corner_radius=8)
            row_f.grid(row=4 + i, column=0, padx=12, pady=2, sticky="ew")
            row_f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(row_f, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"], width=110, anchor="w").grid(
                row=0, column=0, padx=(12, 6), pady=8, sticky="w")
            ctk.CTkLabel(row_f, text=val, font=("Segoe UI", 11, "bold"),
                         text_color=COLORS["text_label"], anchor="w").grid(
                row=0, column=1, padx=(0, 12), pady=8, sticky="w")

        # Espacamento inferior
        ctk.CTkFrame(self._id_card, fg_color="transparent", height=12).grid(
            row=20, column=0)

    # ------------------------------------------------------------------
    def _draw_vitals(self, p):
        for w in self._vitals_card.winfo_children():
            w.destroy()
        self._vitals_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self._vitals_card, text="VIDA & MANA",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=20, pady=(18, 6), sticky="w")
        ctk.CTkFrame(self._vitals_card, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=20, pady=(0, 18))

        hp_pct   = max(0.0, min(1.0, p["hp"]   / max(p["hp_max"],   1)))
        mana_pct = max(0.0, min(1.0, p["mana"] / max(p["mana_max"], 1)))

        # Bloco HP
        self._vital_block(
            parent=self._vitals_card,
            row=2,
            icon="\u2764",
            label="HP",
            current=p["hp"],
            maximum=p["hp_max"],
            pct=hp_pct,
            bar_color=COLORS["hp_red"],
            bar_bg=COLORS["hp_bg"],
            val_color=COLORS["hp_red"],
        )

        ctk.CTkFrame(self._vitals_card, fg_color=COLORS["border"], height=1).grid(
            row=3, column=0, sticky="ew", padx=20, pady=14)

        # Bloco Mana
        self._vital_block(
            parent=self._vitals_card,
            row=4,
            icon="\u26A1",
            label="Mana",
            current=p["mana"],
            maximum=p["mana_max"],
            pct=mana_pct,
            bar_color=COLORS["mana_blue"],
            bar_bg=COLORS["mana_bg"],
            val_color=COLORS["mana_blue"],
        )

        ctk.CTkFrame(self._vitals_card, fg_color="transparent", height=16).grid(
            row=5, column=0)

    def _vital_block(self, parent, row, icon, label, current, maximum, pct,
                     bar_color, bar_bg, val_color):
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row, column=0, padx=20, pady=0, sticky="ew")
        block.grid_columnconfigure(1, weight=1)

        # Icone
        ctk.CTkLabel(block, text=icon, font=("Segoe UI", 28),
                     text_color=val_color, width=44).grid(
            row=0, column=0, rowspan=2, padx=(0, 14), sticky="ns")

        # Label + percentual
        lbl_frame = ctk.CTkFrame(block, fg_color="transparent")
        lbl_frame.grid(row=0, column=1, sticky="ew")
        lbl_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(lbl_frame, text=label, font=("Segoe UI", 13, "bold"),
                     text_color=COLORS["text_label"]).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(lbl_frame, text=f"{pct * 100:.0f}%",
                     font=("Segoe UI", 12, "bold"),
                     text_color=val_color).grid(row=0, column=1, sticky="e")

        # Barra de progresso
        bar = ctk.CTkProgressBar(block, height=14, corner_radius=7,
                                  fg_color=bar_bg, progress_color=bar_color)
        bar.set(pct)
        bar.grid(row=1, column=1, pady=(6, 0), sticky="ew")

        # Valor numerico
        ctk.CTkLabel(block,
                     text=f"{current:,} / {maximum:,}".replace(",", "."),
                     font=("Segoe UI", 20, "bold"),
                     text_color=val_color).grid(
            row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")
