"""
Aba de Status do TibiaBot 860.

Usa StringVar / DoubleVar para atualizar os valores sem destruir
nem recriar widgets — elimina o flickering causado pelo destroy/rebuild
a cada tick do BotEngine (150ms).
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class StatusTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Variaveis reativas -- atualizadas por refresh() sem recriar widgets
        self._var_name     = ctk.StringVar(value="--")
        self._var_vocation = ctk.StringVar(value="--")
        self._var_level    = ctk.StringVar(value="0")
        self._var_stamina  = ctk.StringVar(value="0h 00m")
        self._var_capacity = ctk.StringVar(value="0 oz")
        self._var_pos      = ctk.StringVar(value="X 0   Y 0   Z 0")

        self._var_hp_pct   = ctk.StringVar(value="0%")
        self._var_hp_val   = ctk.StringVar(value="0 / 1")
        self._var_hp_bar   = ctk.DoubleVar(value=0.0)

        self._var_mana_pct = ctk.StringVar(value="0%")
        self._var_mana_val = ctk.StringVar(value="0 / 1")
        self._var_mana_bar = ctk.DoubleVar(value=0.0)

        self._build()
        self.refresh()

    # ------------------------------------------------------------------
    # Construcao (executada uma unica vez)
    # ------------------------------------------------------------------

    def _build(self):
        # --- Header ---
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=28, pady=(22, 0), sticky="ew")
        ctk.CTkLabel(
            hdr, text="Status do Personagem",
            font=("Segoe UI", 22, "bold"), text_color=COLORS["text_primary"]
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text="Leitura em tempo real da memoria",
            font=FONTS["small"], text_color=COLORS["text_faint"]
        ).pack(side="left", padx=(14, 0), pady=(6, 0))

        # --- Separador ---
        ctk.CTkFrame(self, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=28, pady=(10, 0)
        )

        # --- Corpo ---
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.grid(row=2, column=0, padx=28, pady=18, sticky="nsew")
        body.grid_columnconfigure(0, weight=3)
        body.grid_columnconfigure(1, weight=4)
        body.grid_rowconfigure(0, weight=1)

        id_card      = self._make_card(body, 0, 0, padx=(0, 10))
        vitals_card  = self._make_card(body, 0, 1, padx=(10, 0))

        self._build_id_card(id_card)
        self._build_vitals_card(vitals_card)

    def _make_card(self, parent, row, col, padx=(0, 0)):
        card = ctk.CTkFrame(
            parent, fg_color=COLORS["bg_card"],
            corner_radius=16, border_width=1, border_color=COLORS["border"]
        )
        card.grid(row=row, column=col, padx=padx, pady=0, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        return card

    def _build_id_card(self, card):
        # Titulo
        ctk.CTkLabel(
            card, text="IDENTIDADE",
            font=FONTS["badge"], text_color=COLORS["accent_light"]
        ).grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=20, pady=(0, 12)
        )

        # Nome e vocacao
        ctk.CTkLabel(
            card, textvariable=self._var_name,
            font=("Segoe UI", 18, "bold"), text_color=COLORS["text_primary"]
        ).grid(row=2, column=0, padx=20, pady=(0, 2), sticky="w")
        ctk.CTkLabel(
            card, textvariable=self._var_vocation,
            font=FONTS["body"], text_color=COLORS["accent_light"]
        ).grid(row=3, column=0, padx=20, pady=(0, 16), sticky="w")

        # Atributos em grade
        attrs = [
            ("\u2B50  Nivel",          self._var_level),
            ("\u23F1  Stamina",        self._var_stamina),
            ("\U0001F4E6  Capacidade", self._var_capacity),
            ("\U0001F4CD  Posicao",    self._var_pos),
        ]
        for i, (lbl, var) in enumerate(attrs):
            bg = COLORS["bg_panel"] if i % 2 == 0 else "transparent"
            row_f = ctk.CTkFrame(card, fg_color=bg, corner_radius=8)
            row_f.grid(row=4 + i, column=0, padx=12, pady=2, sticky="ew")
            row_f.grid_columnconfigure(1, weight=1)
            ctk.CTkLabel(
                row_f, text=lbl, font=FONTS["small"],
                text_color=COLORS["text_faint"], width=110, anchor="w"
            ).grid(row=0, column=0, padx=(12, 6), pady=8, sticky="w")
            ctk.CTkLabel(
                row_f, textvariable=var,
                font=("Segoe UI", 11, "bold"),
                text_color=COLORS["text_label"], anchor="w"
            ).grid(row=0, column=1, padx=(0, 12), pady=8, sticky="w")

        ctk.CTkFrame(card, fg_color="transparent", height=12).grid(row=20, column=0)

    def _build_vitals_card(self, card):
        # Titulo
        ctk.CTkLabel(
            card, text="VIDA & MANA",
            font=FONTS["badge"], text_color=COLORS["accent_light"]
        ).grid(row=0, column=0, padx=20, pady=(18, 6), sticky="w")
        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).grid(
            row=1, column=0, sticky="ew", padx=20, pady=(0, 18)
        )

        self._build_vital_block(
            card, row=2,
            icon="\u2764", label="HP",
            var_pct=self._var_hp_pct,
            var_val=self._var_hp_val,
            var_bar=self._var_hp_bar,
            bar_color=COLORS["hp_red"],
            bar_bg=COLORS["hp_bg"],
            val_color=COLORS["hp_red"],
        )

        ctk.CTkFrame(card, fg_color=COLORS["border"], height=1).grid(
            row=3, column=0, sticky="ew", padx=20, pady=14
        )

        self._build_vital_block(
            card, row=4,
            icon="\u26A1", label="Mana",
            var_pct=self._var_mana_pct,
            var_val=self._var_mana_val,
            var_bar=self._var_mana_bar,
            bar_color=COLORS["mana_blue"],
            bar_bg=COLORS["mana_bg"],
            val_color=COLORS["mana_blue"],
        )

        ctk.CTkFrame(card, fg_color="transparent", height=16).grid(row=5, column=0)

    def _build_vital_block(self, parent, row, icon, label,
                           var_pct, var_val, var_bar,
                           bar_color, bar_bg, val_color):
        block = ctk.CTkFrame(parent, fg_color="transparent")
        block.grid(row=row, column=0, padx=20, pady=0, sticky="ew")
        block.grid_columnconfigure(1, weight=1)

        # Icone
        ctk.CTkLabel(
            block, text=icon, font=("Segoe UI", 28),
            text_color=val_color, width=44
        ).grid(row=0, column=0, rowspan=2, padx=(0, 14), sticky="ns")

        # Linha label + percentual
        lbl_frame = ctk.CTkFrame(block, fg_color="transparent")
        lbl_frame.grid(row=0, column=1, sticky="ew")
        lbl_frame.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            lbl_frame, text=label,
            font=("Segoe UI", 13, "bold"), text_color=COLORS["text_label"]
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            lbl_frame, textvariable=var_pct,
            font=("Segoe UI", 12, "bold"), text_color=val_color
        ).grid(row=0, column=1, sticky="e")

        # Barra de progresso
        bar = ctk.CTkProgressBar(
            block, height=14, corner_radius=7,
            fg_color=bar_bg, progress_color=bar_color,
            variable=var_bar,
        )
        bar.grid(row=1, column=1, pady=(6, 0), sticky="ew")

        # Valor absoluto
        ctk.CTkLabel(
            block, textvariable=var_val,
            font=("Segoe UI", 20, "bold"), text_color=val_color
        ).grid(row=2, column=0, columnspan=2, pady=(10, 0), sticky="w")

    # ------------------------------------------------------------------
    # Atualizacao de dados (sem recriar widgets)
    # ------------------------------------------------------------------

    def refresh(self):
        """
        Atualiza as variaveis com os dados atuais de _player_data.
        Chamado pelo BotApp via root.after() — sempre na thread principal.
        """
        p = self.app._player_data

        # Identidade
        self._var_name.set(p.get("name", "--") or "--")
        self._var_vocation.set(p.get("vocation", "--") or "--")
        self._var_level.set(str(p.get("level", 0)))

        stamina = p.get("stamina", 0) or 0
        self._var_stamina.set(f"{stamina // 60}h {stamina % 60:02d}m")

        cap = (p.get("capacity", 0) or 0) / 100
        self._var_capacity.set(f"{cap:.0f} oz")

        self._var_pos.set(
            f"X {p.get('x', 0)}   Y {p.get('y', 0)}   Z {p.get('z', 0)}"
        )

        # Vitals — HP
        hp     = max(0, p.get("hp", 0) or 0)
        hp_max = max(1, p.get("hp_max", 1) or 1)
        hp_pct = hp / hp_max
        self._var_hp_pct.set(f"{hp_pct * 100:.0f}%")
        self._var_hp_val.set(f"{hp:,} / {hp_max:,}".replace(",", "."))
        self._var_hp_bar.set(hp_pct)

        # Vitals — Mana
        mana     = max(0, p.get("mana", 0) or 0)
        mana_max = max(1, p.get("mana_max", 1) or 1)
        mana_pct = mana / mana_max
        self._var_mana_pct.set(f"{mana_pct * 100:.0f}%")
        self._var_mana_val.set(f"{mana:,} / {mana_max:,}".replace(",", "."))
        self._var_mana_bar.set(mana_pct)
