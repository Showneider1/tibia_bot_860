import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class StatusTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._var_name     = ctk.StringVar(value="--")
        self._var_vocation = ctk.StringVar(value="--")
        self._var_level    = ctk.StringVar(value="0")
        self._var_stamina  = ctk.StringVar(value="0h 00m")
        self._var_capacity = ctk.StringVar(value="0 oz")
        self._var_pos      = ctk.StringVar(value="X 0  Y 0  Z 0")

        self._var_hp_pct   = ctk.StringVar(value="0%")
        self._var_hp_val   = ctk.StringVar(value="0 / 1")
        self._var_hp_bar   = ctk.DoubleVar(value=0.0)

        self._var_mana_pct = ctk.StringVar(value="0%")
        self._var_mana_val = ctk.StringVar(value="0 / 1")
        self._var_mana_bar = ctk.DoubleVar(value=0.0)

        self._build()
        self.refresh()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=20, pady=(16, 0), sticky="ew")
        ctk.CTkLabel(
            hdr, text="Status", font=("Segoe UI", 18, "bold"),
            text_color=COLORS["text_primary"]
        ).pack(side="left")

        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=20, pady=(8, 0))

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, padx=20, pady=12, sticky="nsew")
        body.grid_columnconfigure(0, weight=2)
        body.grid_columnconfigure(1, weight=3)
        body.grid_rowconfigure(0, weight=1)

        id_card     = self._make_card(body, 0, 0, padx=(0, 8))
        vitals_card = self._make_card(body, 0, 1, padx=(8, 0))

        self._build_id_card(id_card)
        self._build_vitals_card(vitals_card)

    def _make_card(self, parent, row, col, padx=(0, 0)):
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"],
            corner_radius=12, border_width=1, border_color=COLORS["border"]
        )
        card.grid(row=row, column=col, padx=padx, pady=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        return card

    def _build_id_card(self, card):
        ctk.CTkLabel(
            card, text="PERSONAGEM",
            font=FONTS["badge"], text_color=COLORS["accent_light"]
        ).grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        ctk.CTkLabel(
            card, textvariable=self._var_name,
            font=("Segoe UI", 16, "bold"), text_color=COLORS["text_primary"]
        ).grid(row=2, column=0, padx=16, pady=(0, 1), sticky="w")
        ctk.CTkLabel(
            card, textvariable=self._var_vocation,
            font=FONTS["body"], text_color=COLORS["accent_light"]
        ).grid(row=3, column=0, padx=16, pady=(0, 12), sticky="w")

        attrs = [
            ("\u2B50  Level",     self._var_level),
            ("\u23F1  Stamina",   self._var_stamina),
            ("\U0001F4E6  Cap",   self._var_capacity),
            ("\U0001F4CD  Pos",   self._var_pos),
        ]
        for i, (lbl, var) in enumerate(attrs):
            bg = COLORS["bg_panel"] if i % 2 == 0 else "transparent"
            row_f = ctk.CTkFrame(card, fg_color=bg, corner_radius=6)
            row_f.grid(row=4 + i, column=0, padx=10, pady=1, sticky="ew")
            row_f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row_f, text=lbl, font=FONTS["small"],
                text_color=COLORS["text_faint"], width=80, anchor="w"
            ).grid(row=0, column=0, padx=(10, 4), pady=6, sticky="w")
            ctk.CTkLabel(
                row_f, textvariable=var,
                font=("Segoe UI", 10, "bold"),
                text_color=COLORS["text_label"], anchor="w"
            ).grid(row=0, column=1, padx=(0, 10), pady=6, sticky="w")

        ctk.CTkFrame(card, fg_color="transparent", height=10).grid(row=20, column=0)

    def _build_vitals_card(self, card):
        ctk.CTkLabel(
            card, text="VIDA & MANA",
            font=FONTS["badge"], text_color=COLORS["accent_light"]
        ).grid(row=0, column=0, padx=16, pady=(14, 4), sticky="w")
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=16, pady=(0, 14))

        self._build_vital_block(
            card, row=2,
            icon="\u2764", label="HP",
            var_pct=self._var_hp_pct, var_val=self._var_hp_val, var_bar=self._var_hp_bar,
            bar_color=COLORS["hp_red"], bar_bg=COLORS["hp_bg"], val_color=COLORS["hp_red"],
        )

        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).grid(
            row=3, column=0, sticky="ew", padx=16, pady=10)

        self._build_vital_block(
            card, row=4,
            icon="\u26A1", label="Mana",
            var_pct=self._var_mana_pct, var_val=self._var_mana_val, var_bar=self._var_mana_bar,
            bar_color=COLORS["mana_blue"], bar_bg=COLORS["mana_bg"], val_color=COLORS["mana_blue"],
        )

        ctk.CTkFrame(card, fg_color="transparent", height=12).grid(row=5, column=0)

    def _build_vital_block(self, parent, row, icon, label,
                           var_pct, var_val, var_bar,
                           bar_color, bar_bg, val_color):
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row, column=0, padx=16, pady=0, sticky="ew")
        block.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            block, text=icon, font=("Segoe UI", 24),
            text_color=val_color, width=36
        ).grid(row=0, column=0, rowspan=2, padx=(0, 10), sticky="ns")

        lbl_frame = ctk.CTkFrame(block, fg_color="transparent")
        lbl_frame.grid(row=0, column=1, sticky="ew")
        lbl_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            lbl_frame, text=label,
            font=("Segoe UI", 12, "bold"), text_color=COLORS["text_label"]
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            lbl_frame, textvariable=var_pct,
            font=("Segoe UI", 11, "bold"), text_color=val_color
        ).grid(row=0, column=1, sticky="e")

        bar = ctk.CTkProgressBar(
            block, height=12, corner_radius=6,
            fg_color=bar_bg, progress_color=bar_color, variable=var_bar,
        )
        bar.grid(row=1, column=1, pady=(4, 0), sticky="ew")

        ctk.CTkLabel(
            block, textvariable=var_val,
            font=("Segoe UI", 18, "bold"), text_color=val_color
        ).grid(row=2, column=0, columnspan=2, pady=(6, 0), sticky="w")

    def refresh(self):
        p = self.app._player_data

        self._var_name.set(p.get("name", "--") or "--")
        self._var_vocation.set(p.get("vocation", "--") or "--")
        self._var_level.set(str(p.get("level", 0)))

        stamina = p.get("stamina", 0) or 0
        self._var_stamina.set(f"{stamina // 60}h {stamina % 60:02d}m")
        cap = (p.get("capacity", 0) or 0) / 100
        self._var_capacity.set(f"{cap:.0f} oz")
        self._var_pos.set(f"X {p.get('x', 0)}  Y {p.get('y', 0)}  Z {p.get('z', 0)}")

        hp = max(0, p.get("hp", 0) or 0)
        hp_max = max(1, p.get("hp_max", 1) or 1)
        hp_pct = hp / hp_max
        self._var_hp_pct.set(f"{hp_pct * 100:.0f}%")
        self._var_hp_val.set(f"{hp:,} / {hp_max:,}".replace(",", "."))
        self._var_hp_bar.set(hp_pct)

        mana = max(0, p.get("mana", 0) or 0)
        mana_max = max(1, p.get("mana_max", 1) or 1)
        mana_pct = mana / mana_max
        self._var_mana_pct.set(f"{mana_pct * 100:.0f}%")
        self._var_mana_val.set(f"{mana:,} / {mana_max:,}".replace(",", "."))
        self._var_mana_bar.set(mana_pct)
