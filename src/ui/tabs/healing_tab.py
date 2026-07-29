import customtkinter as ctk
from src.ui.theme import COLORS, FONTS


class HealingTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._vars: dict = {}
        self._build()

    def _get_script(self):
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        se = getattr(engine, "script_engine", None)
        if se is None:
            return None
        return se.get_script("HealingBot")

    def _apply_to_script(self, key: str, cast=str) -> None:
        script = self._get_script()
        if script is None:
            return
        var = self._vars.get(key)
        if var is None:
            return
        try:
            script.config[key] = cast(var.get())
            self._schedule_profile_save()
        except (ValueError, TypeError):
            pass

    def _schedule_profile_save(self) -> None:
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return
        pm = getattr(engine, "_profile_manager", None)
        if pm is None:
            return
        player = getattr(engine, "player", None)
        if player is None:
            return
        pm.schedule_save(player.name, engine.script_engine)

    def _read_from_script(self) -> None:
        script = self._get_script()
        if script is None:
            return
        mapping = {
            "hp_threshold":    ("hp_pct",      str),
            "hp_light":        ("hp_light",     str),
            "hp_strong":       ("hp_strong",    str),
            "hp_ultimate":     ("hp_ultimate",  str),
            "mana_threshold":  ("mana_pct",     str),
            "spell_light":     ("spell_light",  str),
            "spell_strong":    ("spell_strong", str),
            "spell_ultimate":  ("spell_ult",    str),
            "spell_mana_drain":("spell_mana",   str),
            "mana_min_for_sd": ("mana_min",     float),
            "cooldown":        ("cooldown",      str),
            "dps_threshold":   ("dps_thresh",   str),
        }
        for cfg_key, (var_key, _) in mapping.items():
            var = self._vars.get(var_key)
            if var and cfg_key in script.config:
                var.set(str(script.config[cfg_key]))

    def _build(self):
        ctk.CTkLabel(self, text="Healing", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(self, text="Cura automatica de HP e Mana",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")

        ctk.CTkButton(
            self, text="Carregar do Script", font=FONTS["small"],
            height=24, corner_radius=6,
            fg_color=COLORS["bg_panel"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent_light"],
            command=self._read_from_script,
        ).grid(row=0, column=1, padx=16, pady=(14, 2), sticky="e")

        self._hp_card(row=2, col=0)
        self._mana_card(row=2, col=1)
        self._spell_card(row=3)

    def _entry(self, parent, row, col, label, var_key, default, cfg_key=None, cast=float,
                padx_l=(12, 6), padx_r=(0, 12)):
        var = ctk.StringVar(value=default)
        self._vars[var_key] = var

        ctk.CTkLabel(parent, text=label, font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=row, column=0, padx=padx_l, pady=3, sticky="w")
        entry = ctk.CTkEntry(
            parent, textvariable=var, height=28, corner_radius=6,
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_label"], font=FONTS["body"],
        )
        entry.grid(row=row, column=1, padx=padx_r, pady=3, sticky="ew")

        if cfg_key:
            entry.bind("<FocusOut>", lambda e: self._apply_to_script(cfg_key, cast))
            entry.bind("<Return>",   lambda e: self._apply_to_script(cfg_key, cast))
        return entry

    def _hp_card(self, row, col):
        card = self._card(row, col, "AUTO-HEAL (HP)")
        card.grid_columnconfigure(1, weight=1)

        self._enabled_hp = ctk.BooleanVar(value=True)
        sw = ctk.CTkSwitch(
            card, text="Ativo", variable=self._enabled_hp,
            font=FONTS["small"], text_color=COLORS["text_label"],
            progress_color=COLORS["hp_red"],
            command=lambda: self._apply_bool_to_script("enable_dps_healing", self._enabled_hp),
        )
        sw.grid(row=1, column=0, columnspan=2, padx=12, pady=(4, 8), sticky="w")

        self._entry(card, 2, 0, "Usar abaixo de (%)",  "hp_pct",      "60",  "hp_threshold",   float)
        self._entry(card, 3, 0, "Spell leve",           "spell_light", "exura","spell_light",   str)
        self._entry(card, 4, 0, "Spell forte",          "spell_strong","exura gran", "spell_strong", str)
        self._entry(card, 5, 0, "Cooldown (s)",         "cooldown",    "0.8", "cooldown",        float)

    def _mana_card(self, row, col):
        card = self._card(row, col, "AUTO-MANA")
        card.grid_columnconfigure(1, weight=1)

        self._enabled_mana = ctk.BooleanVar(value=True)
        ctk.CTkSwitch(
            card, text="Ativo", variable=self._enabled_mana,
            font=FONTS["small"], text_color=COLORS["text_label"],
            progress_color=COLORS["mana_blue"],
        ).grid(row=1, column=0, columnspan=2, padx=12, pady=(4, 8), sticky="w")

        self._entry(card, 2, 0, "Usar abaixo de (%)", "mana_pct",   "40",         "mana_threshold",  float)
        self._entry(card, 3, 0, "Spell mana drain",   "spell_mana", "exura sio",  "spell_mana_drain",str)
        self._entry(card, 4, 0, "Min mana p/ drain (%)","mana_min", "25",         "mana_min_for_sd", float)
        self._entry(card, 5, 0, "DPS threshold",      "dps_thresh", "80",         "dps_threshold",   float)

    def _spell_card(self, row):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=0, columnspan=2, padx=16, pady=(6, 16), sticky="nsew")
        card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(card, text="SPELLS DE EMERGENCIA",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(10, 6), sticky="w")

        specs = [
            ("Critico HP",    "spell_ult",  "exura vita",       "hp_ultimate",  "20"),
            ("Critico Mana",  "spell_ult2", "exura gran mas",   "hp_mana",      "15"),
            ("Ult. Recurso",  "spell_sac",  "utana vid",        "hp_sac",       "10"),
        ]
        for c, (lbl, sk, sv, pk, pv) in enumerate(specs):
            ctk.CTkLabel(card, text=lbl, font=FONTS["subhead"],
                         text_color=COLORS["text_label"]).grid(row=1, column=c, padx=10, pady=2)

            sv_var = ctk.StringVar(value=sv)
            self._vars[sk] = sv_var
            spell_e = ctk.CTkEntry(
                card, textvariable=sv_var, height=28, corner_radius=6,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            )
            spell_e.grid(row=2, column=c, padx=8, pady=2, sticky="ew")

            pct_var = ctk.StringVar(value=pv)
            self._vars[pk] = pct_var
            pct_e = ctk.CTkEntry(
                card, textvariable=pct_var, height=28, corner_radius=6,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            )
            pct_e.grid(row=3, column=c, padx=8, pady=2, sticky="ew")

    def _apply_bool_to_script(self, key: str, var: ctk.BooleanVar) -> None:
        script = self._get_script()
        if script:
            script.config[key] = var.get()
            self._schedule_profile_save()

    def _card(self, row, col, title):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.grid(
            row=row, column=col,
            padx=(16 if col == 0 else 6, 6 if col == 0 else 16),
            pady=(0, 6), sticky="nsew",
        )
        ctk.CTkLabel(card, text=title, font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 2), sticky="w")
        return card
