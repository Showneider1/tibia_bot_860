import customtkinter as ctk
from src.ui.theme import COLORS, FONTS
from src.application.scripts.persistent_script import (
    PersistentRule,
    _CONDITION_DESCRIPTIONS,
    _ACTION_DESCRIPTIONS,
    _CONDITION_PARAM_LABELS,
    _ACTION_PARAM_LABELS,
)

_DEFAULT_CONDITIONS = sorted(_CONDITION_DESCRIPTIONS.keys())
_DEFAULT_ACTIONS = sorted(_ACTION_DESCRIPTIONS.keys())


class PersistentTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._selected_index: int | None = None
        self._build()

    def _get_script(self):
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        se = getattr(engine, "script_engine", None)
        if se is None:
            return None
        return se.get_script("Persistent")

    def _schedule_save(self):
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

    def _load_rules(self):
        script = self._get_script()
        if script is None:
            return []
        return list(script.config.get("rules", []))

    def _build(self):
        ctk.CTkLabel(self, text="Persistent", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(self, text="Regras condicao + acao (ElfBot-style)",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=16, pady=(0, 6))
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self._build_list(content)
        self._build_editor(content)
        self._refresh_list()

    def _build_list(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"], width=280)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frame.grid_propagate(False)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="REGRAS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        canvas = ctk.CTkScrollableFrame(frame, fg_color="transparent", corner_radius=0)
        canvas.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 2))
        canvas.grid_columnconfigure(0, weight=1)
        self._list_canvas = canvas

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 10))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_frame, text="+ Nova regra", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="white", command=self._add_rule).grid(
            row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(btn_frame, text="- Remover", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color="#c0392b", hover_color="#96281b",
                      text_color="white", command=self._remove_rule).grid(
            row=0, column=1, padx=(3, 0), sticky="ew")

    def _build_editor(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color=COLORS["bg_card"],
                                        corner_radius=12, border_width=1,
                                        border_color=COLORS["border"])
        scroll.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        scroll.grid_columnconfigure((0, 1), weight=1)
        self._editor_scroll = scroll

        ctk.CTkLabel(scroll, text="EDITAR REGRA", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        ctk.CTkLabel(scroll, text="Nome:", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=1, column=0, padx=12, pady=3, sticky="w")
        self._ed_name = ctk.CTkEntry(scroll, height=28, corner_radius=6,
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                      text_color=COLORS["text_label"], font=FONTS["body"])
        self._ed_name.grid(row=1, column=1, padx=12, pady=3, sticky="ew")

        ctk.CTkLabel(scroll, text="Cooldown (s):", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=2, column=0, padx=12, pady=3, sticky="w")
        self._ed_cooldown = ctk.CTkEntry(scroll, height=28, corner_radius=6,
                                          fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                          text_color=COLORS["text_label"], font=FONTS["body"])
        self._ed_cooldown.grid(row=2, column=1, padx=12, pady=3, sticky="ew")

        sep = ctk.CTkFrame(scroll, fg_color=COLORS["border"], height=1)
        sep.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        ctk.CTkLabel(scroll, text="CONDICAO", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=4, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")

        self._condition_var = ctk.StringVar(value="always")
        self._condition_menu = ctk.CTkOptionMenu(
            scroll, values=_DEFAULT_CONDITIONS, variable=self._condition_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["accent"],
            text_color=COLORS["text_label"], font=FONTS["small"])
        self._condition_menu.grid(row=5, column=0, columnspan=2, padx=12, pady=3, sticky="ew")
        self._condition_menu.configure(command=lambda v: self._on_condition_change(v))

        self._condition_params_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._condition_params_frame.grid(row=6, column=0, columnspan=2, padx=12, pady=3, sticky="ew")
        self._condition_params_frame.grid_columnconfigure(1, weight=1)
        self._condition_widgets: dict = {}

        sep2 = ctk.CTkFrame(scroll, fg_color=COLORS["border"], height=1)
        sep2.grid(row=7, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        ctk.CTkLabel(scroll, text="ACAO", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=8, column=0, columnspan=2, padx=12, pady=(0, 4), sticky="w")

        self._action_var = ctk.StringVar(value="log")
        self._action_menu = ctk.CTkOptionMenu(
            scroll, values=_DEFAULT_ACTIONS, variable=self._action_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["accent"],
            text_color=COLORS["text_label"], font=FONTS["small"])
        self._action_menu.grid(row=9, column=0, columnspan=2, padx=12, pady=3, sticky="ew")
        self._action_menu.configure(command=lambda v: self._on_action_change(v))

        self._action_params_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        self._action_params_frame.grid(row=10, column=0, columnspan=2, padx=12, pady=3, sticky="ew")
        self._action_params_frame.grid_columnconfigure(1, weight=1)
        self._action_widgets: dict = {}

        ctk.CTkButton(scroll, text="Aplicar", font=FONTS["small"],
                       height=30, corner_radius=8,
                       fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                       text_color="white", command=self._apply_editor).grid(
            row=11, column=0, columnspan=2, padx=12, pady=(10, 14))

    def _refresh_list(self):
        for w in self._list_canvas.winfo_children():
            w.destroy()
        rules = self._load_rules()
        for i, rule_data in enumerate(rules):
            if isinstance(rule_data, dict):
                rule = PersistentRule(**rule_data)
            else:
                rule = rule_data
            row = ctk.CTkFrame(self._list_canvas, fg_color="transparent")
            row.grid(sticky="ew", pady=1)
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(2, weight=1)
            row._rule_data = rule_data if isinstance(rule_data, dict) else rule.__dict__

            enabled = rule.enabled
            dot_color = COLORS["online_green"] if enabled else COLORS["text_faint"]
            dot = ctk.CTkLabel(row, text="\u25cf", font=("Segoe UI", 9),
                                text_color=dot_color, width=14)
            dot.grid(row=0, column=0, padx=(6, 1), pady=4)
            dot.bind("<Button-1>", lambda e, idx=i: self._toggle_enabled(idx))

            ctk.CTkLabel(row, text=rule.name or f"Regra {i+1}",
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLORS["text_primary"]).grid(
                row=0, column=1, padx=(0, 2), sticky="w")

            ct_desc = _CONDITION_DESCRIPTIONS.get(rule.condition_type, rule.condition_type)
            at_desc = _ACTION_DESCRIPTIONS.get(rule.action_type, rule.action_type)
            ctk.CTkLabel(row, text=f"{ct_desc} -> {at_desc}", font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=0, column=2, padx=(2, 6), sticky="e")

            row.bind("<Button-1>", lambda e, idx=i: self._select_rule(idx))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, idx=i: self._select_rule(idx))

    def _toggle_enabled(self, index: int):
        rules = self._load_rules()
        if 0 <= index < len(rules):
            r = rules[index]
            if isinstance(r, dict):
                r["enabled"] = not r.get("enabled", True)
            else:
                r.enabled = not r.enabled
        script = self._get_script()
        if script:
            script.config["rules"] = rules
            self._schedule_save()
        self._refresh_list()

    def _select_rule(self, index: int):
        self._selected_index = index
        rules = self._load_rules()
        if index >= len(rules):
            return
        rule_data = rules[index]
        rule = PersistentRule(**rule_data) if isinstance(rule_data, dict) else rule_data

        self._ed_name.delete(0, "end")
        self._ed_name.insert(0, rule.name)
        self._ed_cooldown.delete(0, "end")
        self._ed_cooldown.insert(0, str(rule.cooldown))
        self._condition_var.set(rule.condition_type)
        self._action_var.set(rule.action_type)
        self._rebuild_condition_params(rule.condition_type, rule.condition_params)
        self._rebuild_action_params(rule.action_type, rule.action_params)

    def _add_rule(self):
        rules = self._load_rules()
        new_rule = PersistentRule(
            name=f"Regra {len(rules) + 1}",
            condition_type="always",
            action_type="log",
            action_params={"message": "Regra executada"},
        )
        rules.append(new_rule.__dict__)
        script = self._get_script()
        if script:
            script.config["rules"] = rules
            self._schedule_save()
        self._refresh_list()
        self._select_rule(len(rules) - 1)

    def _remove_rule(self):
        if self._selected_index is None:
            return
        rules = self._load_rules()
        if 0 <= self._selected_index < len(rules):
            rules.pop(self._selected_index)
        script = self._get_script()
        if script:
            script.config["rules"] = rules
            self._schedule_save()
        self._selected_index = None
        self._refresh_list()

    def _on_condition_change(self, ct: str):
        self._rebuild_condition_params(ct, {})

    def _on_action_change(self, at: str):
        self._rebuild_action_params(at, {})

    def _rebuild_condition_params(self, ct: str, values: dict):
        for w in self._condition_widgets.values():
            w.destroy()
        self._condition_widgets.clear()
        params = _CONDITION_PARAM_LABELS.get(ct, {})
        for row_i, (param_key, label) in enumerate(params.items()):
            ctk.CTkLabel(self._condition_params_frame, text=label,
                         font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
                row=row_i, column=0, padx=(0, 6), pady=2, sticky="w")
            entry = ctk.CTkEntry(self._condition_params_frame, height=26, corner_radius=6,
                                  fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                  text_color=COLORS["text_label"], font=FONTS["small"])
            entry.grid(row=row_i, column=1, padx=0, pady=2, sticky="ew")
            entry.insert(0, str(values.get(param_key, "")))
            self._condition_widgets[param_key] = entry

    def _rebuild_action_params(self, at: str, values: dict):
        for w in self._action_widgets.values():
            w.destroy()
        self._action_widgets.clear()
        params = _ACTION_PARAM_LABELS.get(at, {})
        for row_i, (param_key, label) in enumerate(params.items()):
            ctk.CTkLabel(self._action_params_frame, text=label,
                         font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
                row=row_i, column=0, padx=(0, 6), pady=2, sticky="w")
            entry = ctk.CTkEntry(self._action_params_frame, height=26, corner_radius=6,
                                  fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                  text_color=COLORS["text_label"], font=FONTS["small"])
            entry.grid(row=row_i, column=1, padx=0, pady=2, sticky="ew")
            entry.insert(0, str(values.get(param_key, "")))
            self._action_widgets[param_key] = entry

    def _apply_editor(self):
        if self._selected_index is None:
            return
        rules = self._load_rules()
        if self._selected_index >= len(rules):
            return

        rule_data = rules[self._selected_index]
        rule = PersistentRule(**rule_data) if isinstance(rule_data, dict) else rule_data

        rule.name = self._ed_name.get().strip() or f"Regra {self._selected_index + 1}"
        try:
            rule.cooldown = max(0.1, float(self._ed_cooldown.get().strip() or 1.0))
        except ValueError:
            rule.cooldown = 1.0
        rule.condition_type = self._condition_var.get()
        rule.condition_params = {k: e.get().strip() for k, e in self._condition_widgets.items()}
        rule.action_type = self._action_var.get()
        rule.action_params = {k: e.get().strip() for k, e in self._action_widgets.items()}
        rule.last_run = 0.0

        rules[self._selected_index] = rule.__dict__
        script = self._get_script()
        if script:
            script.config["rules"] = rules
            self._schedule_save()
        self._refresh_list()
