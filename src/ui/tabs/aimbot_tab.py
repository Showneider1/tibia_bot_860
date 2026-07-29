import customtkinter as ctk
from src.ui.theme import COLORS, FONTS

_DEFAULT_PRIORITIES = [
    {"name": "Demon",           "spell": "exori gran", "distance": 1, "hp_pct": 100, "mode": "Attack", "priority": 1},
    {"name": "Dragon Lord",     "spell": "exori gran", "distance": 1, "hp_pct": 100, "mode": "Attack", "priority": 2},
    {"name": "Dragon",          "spell": "exori hur",  "distance": 3, "hp_pct": 100, "mode": "Attack", "priority": 3},
    {"name": "Giant Spider",    "spell": "exori hur",  "distance": 3, "hp_pct": 100, "mode": "Attack", "priority": 4},
    {"name": "Necromancer",     "spell": "exori",      "distance": 1, "hp_pct": 100, "mode": "Attack", "priority": 5},
    {"name": "Cyclops",         "spell": "exori",      "distance": 1, "hp_pct": 100, "mode": "Attack", "priority": 6},
    {"name": "Rotworm",         "spell": "F1",         "distance": 3, "hp_pct": 80,  "mode": "Attack", "priority": 7},
]


class AimbotTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._vars: dict = {}
        self._selected_index: int | None = None
        self._build()

    def _get_script(self):
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        se = getattr(engine, "script_engine", None)
        if se is None:
            return None
        return se.get_script("AimBot")

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

    def _sync_priorities(self):
        script = self._get_script()
        if script is None:
            return
        priorities = getattr(self, "_priorities_data", _DEFAULT_PRIORITIES)
        script.config["target_priorities"] = list(priorities)
        self._schedule_save()

    def _toggle_enabled(self):
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return
        se = getattr(engine, "script_engine", None)
        if se is None:
            return
        script = se.get_script("AimBot")
        if script is None:
            return
        if self._enabled_var.get():
            se.enable_script("AimBot")
            script.config["enabled"] = True
        else:
            se.disable_script("AimBot")
            script.config["enabled"] = False
        self._schedule_save()

    def _sync_config(self):
        script = self._get_script()
        if script is None:
            return
        script.config["targeting_mode"] = self._vars["target_mode"].get()
        script.config["attack_hotkey"] = self._ed_hotkey.get().strip() or "F1"
        try:
            script.config["min_hp_to_attack"] = int(self._ed_min_hp.get().strip())
        except ValueError:
            pass
        script.config["enable_anti_lure"] = self._anti_lure.get()
        script.config["use_combat_ai"] = self._use_ai.get()
        script.config["use_memory_injection"] = self._use_mem_inj.get()
        try:
            script.config["viewport_offset_x"] = int(self._ed_off_x.get().strip())
        except ValueError:
            pass
        try:
            script.config["viewport_offset_y"] = int(self._ed_off_y.get().strip())
        except ValueError:
            pass
        try:
            script.config["battle_list_x"] = int(self._ed_bl_x.get().strip())
        except ValueError:
            pass
        try:
            script.config["battle_list_y_start"] = int(self._ed_bl_y.get().strip())
        except ValueError:
            pass
        try:
            script.config["battle_list_slot_height"] = int(self._ed_bl_h.get().strip())
        except ValueError:
            pass
        self._schedule_save()

    def _load_priorities(self):
        script = self._get_script()
        if script is None:
            return _DEFAULT_PRIORITIES
        pri = script.config.get("target_priorities")
        if pri:
            return pri
        return _DEFAULT_PRIORITIES

    def _load_config(self):
        script = self._get_script()
        if script is None:
            return
        self._enabled_var.set(script.enabled)
        self._vars["target_mode"].set(script.config.get("targeting_mode", "highest_xp"))
        self._ed_hotkey.delete(0, "end")
        self._ed_hotkey.insert(0, script.config.get("attack_hotkey", "F1"))
        self._ed_min_hp.delete(0, "end")
        self._ed_min_hp.insert(0, str(script.config.get("min_hp_to_attack", 30)))
        self._anti_lure.set(script.config.get("enable_anti_lure", True))
        self._use_ai.set(script.config.get("use_combat_ai", True))
        self._use_mem_inj.set(script.config.get("use_memory_injection", True))
        self._ed_off_x.delete(0, "end")
        self._ed_off_x.insert(0, str(script.config.get("viewport_offset_x", 0)))
        self._ed_off_y.delete(0, "end")
        self._ed_off_y.insert(0, str(script.config.get("viewport_offset_y", 0)))
        self._ed_bl_x.delete(0, "end")
        self._ed_bl_x.insert(0, str(script.config.get("battle_list_x", 470)))
        self._ed_bl_y.delete(0, "end")
        self._ed_bl_y.insert(0, str(script.config.get("battle_list_y_start", 42)))
        self._ed_bl_h.delete(0, "end")
        self._ed_bl_h.insert(0, str(script.config.get("battle_list_slot_height", 16)))

    def update_from_script(self):
        self._priorities_data = self._load_priorities()
        self._load_config()
        self._refresh_list()

    def _build(self):
        ctk.CTkLabel(self, text="Aimbot", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(self, text="Targeting por prioridade de criatura",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 4), sticky="w")

        self._enabled_var = ctk.BooleanVar(value=False)
        enable_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=8,
                                     border_width=1, border_color=COLORS["border"])
        enable_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 6))
        enable_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(enable_frame, text="Ligar AimBot", font=FONTS["body"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, padx=12, pady=8, sticky="w")
        self._enabled_switch = ctk.CTkSwitch(enable_frame, text="",
                                              variable=self._enabled_var,
                                              onvalue=True, offvalue=False,
                                              progress_color=COLORS["accent"],
                                              command=self._toggle_enabled)
        self._enabled_switch.grid(row=0, column=1, padx=12, pady=8, sticky="e")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=3, column=0, columnspan=2, sticky="nsew", padx=16, pady=(0, 6))
        content.grid_columnconfigure(0, weight=0)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(1, weight=1)

        self._build_priority_list(content)
        self._build_editor(content)
        self._build_settings(content)

        self._load_config()
        self._refresh_list()
        if self._priorities_data:
            self._select_priority(0)

    def _build_priority_list(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"], width=280)
        frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 8))
        frame.grid_propagate(False)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="PRIORIDADES",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        canvas = ctk.CTkScrollableFrame(frame, fg_color="transparent", corner_radius=0)
        canvas.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 2))
        canvas.grid_columnconfigure(0, weight=1)
        self._list_canvas = canvas

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 10))
        btn_frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkButton(btn_frame, text="+ Adicionar", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="white", command=self._add_priority).grid(
            row=0, column=0, padx=(0, 3), sticky="ew")
        ctk.CTkButton(btn_frame, text="- Remover", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color="#c0392b", hover_color="#96281b",
                      text_color="white", command=self._remove_priority).grid(
            row=0, column=1, padx=(3, 0), sticky="ew")

    def _build_editor(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 6))
        frame.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(frame, text="EDITAR ALVO",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        self._ed_name = ctk.CTkEntry(frame, height=28, corner_radius=6,
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                      text_color=COLORS["text_label"], font=FONTS["body"])
        self._ed_spell = ctk.CTkEntry(frame, height=28, corner_radius=6,
                                       fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                       text_color=COLORS["text_label"], font=FONTS["body"])
        self._ed_dist = ctk.CTkEntry(frame, height=28, corner_radius=6,
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                      text_color=COLORS["text_label"], font=FONTS["body"])
        self._ed_hp = ctk.CTkEntry(frame, height=28, corner_radius=6,
                                     fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                     text_color=COLORS["text_label"], font=FONTS["body"])
        self._ed_mode = ctk.StringVar(value="Attack")
        self._ed_mode_menu = ctk.CTkOptionMenu(frame, values=["Attack", "Follow"],
                                                variable=self._ed_mode,
                                                fg_color=COLORS["bg_input"],
                                                button_color=COLORS["accent"],
                                                text_color=COLORS["text_label"],
                                                font=FONTS["small"])
        self._ed_mode_menu.configure(command=lambda v: self._save_selected())
        fields = [
            ("Nome da criatura", self._ed_name, None),
            ("Spell / Hotkey",   self._ed_spell, None),
            ("Distancia maxima", self._ed_dist, None),
            ("HP do alvo (%)",   self._ed_hp, None),
            ("Modo",             None, self._ed_mode_menu),
        ]
        for i, (lbl, entry, menu) in enumerate(fields):
            ctk.CTkLabel(frame, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=i+1, column=0, padx=12, pady=3, sticky="w")
            if entry:
                entry.grid(row=i+1, column=1, padx=12, pady=3, sticky="ew")
                entry.bind("<FocusOut>", lambda e: self._save_selected())
                entry.bind("<Return>", lambda e: self._save_selected())
            if menu:
                menu.grid(row=i+1, column=1, padx=12, pady=3, sticky="ew")

    def _build_settings(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=(6, 0))
        frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        ctk.CTkLabel(frame, text="CONFIGURACOES GLOBAIS",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=4, padx=12, pady=(10, 6), sticky="w")

        ctk.CTkLabel(frame, text="Modo", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=1, column=0, padx=(12, 2), pady=3, sticky="w")
        self._vars["target_mode"] = ctk.StringVar(value="highest_xp")
        self._vars["target_mode"].trace_add("write", lambda *a: self._sync_config())
        ctk.CTkOptionMenu(frame, values=["highest_xp", "lowest_hp", "closest", "highest_threat"],
                           variable=self._vars["target_mode"],
                           fg_color=COLORS["bg_input"], button_color=COLORS["accent"],
                           text_color=COLORS["text_label"], font=FONTS["small"]).grid(
            row=1, column=1, padx=(2, 12), pady=3, sticky="ew")

        ctk.CTkLabel(frame, text="Hotkey atq", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=1, column=2, padx=(12, 2), pady=3, sticky="w")
        self._ed_hotkey = ctk.CTkEntry(frame, height=28, corner_radius=6,
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                        text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_hotkey.grid(row=1, column=3, padx=(2, 12), pady=3, sticky="ew")
        self._ed_hotkey.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_hotkey.bind("<Return>", lambda e: self._sync_config())

        ctk.CTkLabel(frame, text="HP% minimo", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=2, column=0, padx=(12, 2), pady=3, sticky="w")
        self._ed_min_hp = ctk.CTkEntry(frame, height=28, corner_radius=6,
                                        fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                        text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_min_hp.grid(row=2, column=1, padx=(2, 12), pady=3, sticky="ew")
        self._ed_min_hp.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_min_hp.bind("<Return>", lambda e: self._sync_config())

        self._anti_lure = ctk.BooleanVar(value=True)
        self._anti_lure.trace_add("write", lambda *a: self._sync_config())
        ctk.CTkSwitch(frame, text="Anti-lure", variable=self._anti_lure,
                      font=FONTS["small"], text_color=COLORS["text_label"],
                      progress_color=COLORS["accent"]).grid(
            row=2, column=2, padx=(12, 2), pady=3, sticky="w")
        self._use_ai = ctk.BooleanVar(value=True)
        self._use_ai.trace_add("write", lambda *a: self._sync_config())
        ctk.CTkSwitch(frame, text="Combat AI", variable=self._use_ai,
                      font=FONTS["small"], text_color=COLORS["text_label"],
                      progress_color=COLORS["accent"]).grid(
            row=2, column=3, padx=(2, 12), pady=3, sticky="w")

        self._use_mem_inj = ctk.BooleanVar(value=True)
        self._use_mem_inj.trace_add("write", lambda *a: self._sync_config())
        ctk.CTkSwitch(frame, text="Mem. Injection", variable=self._use_mem_inj,
                      font=FONTS["small"], text_color=COLORS["accent_light"],
                      progress_color=COLORS["accent"]).grid(
            row=3, column=0, columnspan=2, padx=(12, 2), pady=3, sticky="w")

        sep = ctk.CTkFrame(frame, height=1, fg_color=COLORS["border"])
        sep.grid(row=4, column=0, columnspan=4, sticky="ew", padx=12, pady=4)

        ctk.CTkLabel(frame, text="CALIBRAGEM TILE CLICK",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=5, column=0, columnspan=4, padx=12, pady=(2, 4), sticky="w")

        ctk.CTkLabel(frame, text="Viewport X", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=6, column=0, padx=(12, 2), pady=2, sticky="w")
        self._ed_off_x = ctk.CTkEntry(frame, height=24, corner_radius=6, width=60,
                                       fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                       text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_off_x.grid(row=6, column=1, padx=(2, 12), pady=2, sticky="w")
        self._ed_off_x.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_off_x.bind("<Return>", lambda e: self._sync_config())

        ctk.CTkLabel(frame, text="Viewport Y", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=6, column=2, padx=(12, 2), pady=2, sticky="w")
        self._ed_off_y = ctk.CTkEntry(frame, height=24, corner_radius=6, width=60,
                                       fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                       text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_off_y.grid(row=6, column=3, padx=(2, 12), pady=2, sticky="w")
        self._ed_off_y.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_off_y.bind("<Return>", lambda e: self._sync_config())

        ctk.CTkLabel(frame, text="CALIBRAGEM BATTLE LIST",
                     font=FONTS["badge"], text_color=COLORS["accent_light"]).grid(
            row=7, column=0, columnspan=4, padx=12, pady=(6, 4), sticky="w")

        ctk.CTkLabel(frame, text="BL X", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=8, column=0, padx=(12, 2), pady=2, sticky="w")
        self._ed_bl_x = ctk.CTkEntry(frame, height=24, corner_radius=6, width=60,
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                      text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_bl_x.grid(row=8, column=1, padx=(2, 12), pady=2, sticky="w")
        self._ed_bl_x.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_bl_x.bind("<Return>", lambda e: self._sync_config())

        ctk.CTkLabel(frame, text="BL Y inicio", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=8, column=2, padx=(12, 2), pady=2, sticky="w")
        self._ed_bl_y = ctk.CTkEntry(frame, height=24, corner_radius=6, width=60,
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                      text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_bl_y.grid(row=8, column=3, padx=(2, 12), pady=2, sticky="w")
        self._ed_bl_y.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_bl_y.bind("<Return>", lambda e: self._sync_config())

        ctk.CTkLabel(frame, text="BL slot h", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(row=9, column=0, padx=(12, 2), pady=2, sticky="w")
        self._ed_bl_h = ctk.CTkEntry(frame, height=24, corner_radius=6, width=60,
                                      fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                                      text_color=COLORS["text_label"], font=FONTS["small"])
        self._ed_bl_h.grid(row=9, column=1, padx=(2, 12), pady=2, sticky="w")
        self._ed_bl_h.bind("<FocusOut>", lambda e: self._sync_config())
        self._ed_bl_h.bind("<Return>", lambda e: self._sync_config())

    def _refresh_list(self):
        self._priorities_data = self._load_priorities()
        for w in self._list_canvas.winfo_children():
            w.destroy()
        for i, pri in enumerate(self._priorities_data):
            row = ctk.CTkFrame(self._list_canvas, fg_color="transparent")
            row.grid(row=i, column=0, sticky="ew", pady=1)
            row.grid_columnconfigure(0, weight=0)
            row.grid_columnconfigure(2, weight=1)

            ctk.CTkLabel(row, text=f"{pri.get('priority', i+1)}.",
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLORS["accent_light"]).grid(
                row=0, column=0, padx=(6, 2), pady=4, sticky="w")
            ctk.CTkLabel(row, text=pri.get("name", "*"),
                         font=("Segoe UI", 11, "bold"),
                         text_color=COLORS["text_primary"]).grid(
                row=0, column=1, padx=(0, 2), sticky="w")
            info = f"{pri.get('spell', 'F1')} | {pri.get('distance', 1)}sqm | {pri.get('hp_pct', 100)}%"
            ctk.CTkLabel(row, text=info, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=0, column=2, padx=(2, 6), sticky="e")

            row.bind("<Button-1>", lambda e, idx=i: self._select_priority(idx))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, idx=i: self._select_priority(idx))

        if not self._priorities_data:
            ctk.CTkLabel(self._list_canvas, text="Nenhum alvo",
                         font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
                row=0, column=0, padx=12, pady=16)

    def _select_priority(self, index):
        self._selected_index = index
        pri = self._priorities_data[index]
        self._ed_name.delete(0, "end")
        self._ed_name.insert(0, pri.get("name", ""))
        self._ed_spell.delete(0, "end")
        self._ed_spell.insert(0, pri.get("spell", "F1"))
        self._ed_dist.delete(0, "end")
        self._ed_dist.insert(0, str(pri.get("distance", 1)))
        self._ed_hp.delete(0, "end")
        self._ed_hp.insert(0, str(pri.get("hp_pct", 100)))
        self._ed_mode.set(pri.get("mode", "Attack"))

    def _save_selected(self):
        if self._selected_index is None:
            return
        pri = self._priorities_data[self._selected_index]
        pri["name"] = self._ed_name.get().strip() or "*"
        pri["spell"] = self._ed_spell.get().strip() or "F1"
        try:
            pri["distance"] = int(self._ed_dist.get().strip())
        except ValueError:
            pri["distance"] = 1
        try:
            pri["hp_pct"] = int(self._ed_hp.get().strip())
        except ValueError:
            pri["hp_pct"] = 100
        pri["mode"] = self._ed_mode.get()
        pri["priority"] = self._selected_index + 1
        self._refresh_list()
        self._select_priority(self._selected_index)
        self._sync_priorities()

    def _add_priority(self):
        new_pri = {"name": "*", "spell": "F1", "distance": 1, "hp_pct": 100, "mode": "Attack",
                    "priority": len(self._priorities_data) + 1}
        self._priorities_data.append(new_pri)
        self._sync_priorities()
        self._refresh_list()
        self._select_priority(len(self._priorities_data) - 1)

    def _remove_priority(self):
        if self._selected_index is None or not self._priorities_data:
            return
        del self._priorities_data[self._selected_index]
        for i, pri in enumerate(self._priorities_data):
            pri["priority"] = i + 1
        self._sync_priorities()
        self._selected_index = None
        self._refresh_list()
