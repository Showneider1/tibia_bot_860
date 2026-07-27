"""
Aba de Healing - configuracao de auto-heal conectada ao HealingScript.

Conexao com o script:
    Todos os campos de entrada chamam _apply_to_script() ao perder foco
    ou ao pressionar Enter, atualizando config do HealingScript em tempo real.
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

        # Variaveis ligadas aos campos de entrada
        self._vars: dict = {}
        self._build()

    # ------------------------------------------------------------------
    # Acesso ao HealingScript via BotEngine
    # ------------------------------------------------------------------

    def _get_script(self):
        """Retorna a instancia de HealingScript do engine, ou None."""
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        scripts = getattr(engine, "scripts", None) or getattr(engine, "_scripts", None)
        if scripts is None:
            return None
        # Suporta lista ou dict {name: script}
        if isinstance(scripts, dict):
            return scripts.get("HealingBot") or scripts.get("healing")
        for s in scripts:
            if getattr(s, "name", "") in ("HealingBot", "healing"):
                return s
        return None

    def _apply_to_script(self, key: str, cast=str) -> None:
        """Sincroniza o campo 'key' com a config do HealingScript."""
        script = self._get_script()
        if script is None:
            return
        var = self._vars.get(key)
        if var is None:
            return
        try:
            value = cast(var.get())
            script.config[key] = value
        except (ValueError, TypeError):
            pass  # valor invalido; nao altera o script

    def _read_from_script(self) -> None:
        """Carrega os valores atuais do HealingScript nos campos da UI."""
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
            "cooldown":        ("cooldown",      str),
            "dps_threshold":   ("dps_thresh",   str),
        }
        for cfg_key, (var_key, _) in mapping.items():
            var = self._vars.get(var_key)
            if var and cfg_key in script.config:
                var.set(str(script.config[cfg_key]))

    # ------------------------------------------------------------------
    # Construcao da UI
    # ------------------------------------------------------------------

    def _build(self):
        ctk.CTkLabel(self, text="Healing", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(self, text="Configure cura automatica de HP e Mana",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        # Botao sincronizar
        ctk.CTkButton(
            self, text="Carregar do Script", font=FONTS["small"],
            height=26, corner_radius=8,
            fg_color=COLORS["bg_panel"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["accent_light"],
            command=self._read_from_script,
        ).grid(row=0, column=1, padx=24, pady=(20, 4), sticky="e")

        self._hp_card(row=2, col=0)
        self._mana_card(row=2, col=1)
        self._spell_card(row=3)

    def _entry(self, parent, row, col, label, var_key, default, cfg_key=None, cast=float,
                padx_l=(16, 8), padx_r=(0, 16)):
        """Cria label + entry com binding automatico ao script."""
        var = ctk.StringVar(value=default)
        self._vars[var_key] = var

        ctk.CTkLabel(parent, text=label, font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=row, column=0, padx=padx_l, pady=5, sticky="w")
        entry = ctk.CTkEntry(
            parent, textvariable=var, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_label"], font=FONTS["body"],
        )
        entry.grid(row=row, column=1, padx=padx_r, pady=5, sticky="ew")

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
            font=FONTS["body"], text_color=COLORS["text_label"],
            progress_color=COLORS["hp_red"],
            command=lambda: self._apply_bool_to_script("enable_dps_healing", self._enabled_hp),
        )
        sw.grid(row=1, column=0, columnspan=2, padx=16, pady=(6, 12), sticky="w")

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
            font=FONTS["body"], text_color=COLORS["text_label"],
            progress_color=COLORS["mana_blue"],
        ).grid(row=1, column=0, columnspan=2, padx=16, pady=(6, 12), sticky="w")

        self._entry(card, 2, 0, "Usar abaixo de (%)", "mana_pct",   "40",         "mana_threshold",  float)
        self._entry(card, 3, 0, "Spell mana drain",   "spell_mana", "exura sio",  "spell_mana_drain",str)
        self._entry(card, 4, 0, "Min mana p/ drain (%)","mana_min", "25",         "mana_min_for_sd", float)
        self._entry(card, 5, 0, "DPS threshold",      "dps_thresh", "80",         "dps_threshold",   float)

    def _spell_card(self, row):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=row, column=0, columnspan=2, padx=24, pady=(8, 24), sticky="nsew")
        card.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(card, text="SPELLS DE EMERGENCIA",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=3, padx=16, pady=(14, 10), sticky="w")

        specs = [
            ("Critico HP",    "spell_ult",  "exura vita",       "hp_ultimate",  "20", "spell_ultimate",  "hp_ultimate"),
            ("Critico Mana",  "spell_ult2", "exura gran mas",   "hp_mana",      "15", "spell_mana_drain","hp_mana_drain"),
            ("Ult. Recurso",  "spell_sac",  "utana vid",        "hp_sac",       "10", "spell_sacrifice", "sacrifice_hp_threshold"),
        ]
        for c, (lbl, sk, sv, pk, pv, scfg_s, scfg_p) in enumerate(specs):
            ctk.CTkLabel(card, text=lbl, font=FONTS["subhead"],
                         text_color=COLORS["text_label"]).grid(row=1, column=c, padx=16, pady=4)

            sv_var = ctk.StringVar(value=sv)
            self._vars[sk] = sv_var
            spell_e = ctk.CTkEntry(
                card, textvariable=sv_var, height=32, corner_radius=8,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            )
            spell_e.grid(row=2, column=c, padx=12, pady=4, sticky="ew")
            spell_e.bind("<FocusOut>", lambda e, k=scfg_s: self._apply_to_script(k, str))
            spell_e.bind("<Return>",   lambda e, k=scfg_s: self._apply_to_script(k, str))

            pct_var = ctk.StringVar(value=pv)
            self._vars[pk] = pct_var
            pct_e = ctk.CTkEntry(
                card, textvariable=pct_var, height=32, corner_radius=8,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            )
            pct_e.grid(row=3, column=c, padx=12, pady=4, sticky="ew")
            pct_e.bind("<FocusOut>", lambda e, k=scfg_p: self._apply_to_script(k, float))
            pct_e.bind("<Return>",   lambda e, k=scfg_p: self._apply_to_script(k, float))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_bool_to_script(self, key: str, var: ctk.BooleanVar) -> None:
        script = self._get_script()
        if script:
            script.config[key] = var.get()

    def _card(self, row, col, title):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(
            row=row, column=col,
            padx=(24 if col == 0 else 8, 8 if col == 0 else 24),
            pady=(0, 8), sticky="nsew",
        )
        ctk.CTkLabel(card, text=title, font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 4), sticky="w")
        return card
