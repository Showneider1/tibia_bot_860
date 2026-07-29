import customtkinter as ctk
from src.ui.theme import COLORS, FONTS

_ITEMS_PRESET = [
    (3031, "Gold Coin"), (3035, "Platinum Coin"), (3034, "Crystal Coin"),
    (3725, "Magic Plate Armor"), (3391, "Magic Sword"), (3274, "Knight Axe"),
    (3356, "Crossbow"), (3509, "Plate Armor"), (3354, "Plate Shield"),
    (3447, "Brown Mushroom"), (3114, "Wand of Inferno"), (3078, "Wand of Decay"),
    (3079, "Wand of Cosmic Energy"), (3074, "Snakebite Rod"), (3075, "Moonlight Rod"),
    (3082, "Hailstorm Rod"),
]


class LooterTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure((0, 1), weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._vars: dict = {}
        self._build()
        self.after(500, self._refresh_stats)

    def _get_script(self):
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        se = getattr(engine, "script_engine", None)
        if se is None:
            return None
        return se.get_script("Looter")

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

    def _apply(self, key, cast=str):
        script = self._get_script()
        if script is None:
            return
        var = self._vars.get(key)
        if var is None:
            return
        try:
            script.config[key] = cast(var.get())
        except (ValueError, TypeError):
            return
        self._schedule_save()

    def _apply_bool(self, key, var):
        script = self._get_script()
        if script:
            script.config[key] = var.get()
            self._schedule_save()

    def _refresh_stats(self):
        script = self._get_script()
        if script is None:
            return
        stats = script.get_loot_stats()
        self._var_looted.set(f"{stats['total_looted']}")
        self._var_pending.set(f"{stats['pending_kills']}")
        self._var_tracked.set(f"{stats['items_tracked']}")
        self.after(2000, self._refresh_stats)

    def _build(self):
        ctk.CTkLabel(self, text="Looter", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(self, text="Auto-loot com tracking de kills",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=16, pady=(0, 6))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=0)
        content.grid_rowconfigure(0, weight=1)

        self._build_left(content)
        self._build_right(content)
        self._build_status(content)

    def _build_left(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(frame, text="CONFIGURACOES", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        fields = [
            ("Raio loot (sqm)",   "loot_radius",              "3",   int),
            ("Delay (s)",         "loot_delay",               "0.5", float),
            ("Max loot/run",      "max_loot_per_run",         "10",  int),
            ("Timeout kill (s)",  "kill_positions_timeout",   "60",  int),
        ]
        for i, (lbl, key, default, cast) in enumerate(fields):
            r = i // 2
            c = (i % 2) * 2
            ctk.CTkLabel(frame, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=r+1, column=c, padx=(12, 2), pady=3, sticky="w")
            self._vars[key] = ctk.StringVar(value=default)
            ctk.CTkEntry(frame, textvariable=self._vars[key],
                         height=28, corner_radius=6, width=60,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"], font=FONTS["small"]).grid(
                row=r+1, column=c+1, padx=(2, 12), pady=3, sticky="w")

        sep = ctk.CTkFrame(frame, fg_color=COLORS["border"], height=1)
        sep.grid(row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        for i, (lbl, key, default) in enumerate([
            ("Hotkey loot",   "loot_hotkey",         "F4"),
            ("Hotkey corpse", "open_corpse_hotkey",  "F5"),
        ]):
            ctk.CTkLabel(frame, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=4+i, column=0, padx=(12, 2), pady=3, sticky="w")
            self._vars[key] = ctk.StringVar(value=default)
            ctk.CTkEntry(frame, textvariable=self._vars[key],
                         height=28, corner_radius=6, width=60,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"], font=FONTS["small"]).grid(
                row=4+i, column=0, padx=(100, 12), pady=3, sticky="w")

        sep2 = ctk.CTkFrame(frame, fg_color=COLORS["border"], height=1)
        sep2.grid(row=6, column=0, columnspan=2, sticky="ew", padx=12, pady=6)

        switches = [
            ("Abrir corpses",   "open_corpses",     True),
            ("Usar hotkey loot","use_hotkey_loot",  True),
            ("Track kills",     "track_kills",      True),
        ]
        for i, (lbl, key, default) in enumerate(switches):
            var = ctk.BooleanVar(value=default)
            self._vars[key] = var
            ctk.CTkSwitch(frame, text=lbl, variable=var,
                          font=FONTS["small"], text_color=COLORS["text_label"],
                          progress_color=COLORS["accent"],
                          command=lambda k=key, v=var: self._apply_bool(k, v)).grid(
                row=7+i, column=0, columnspan=2, padx=12, pady=2, sticky="w")

    def _build_right(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(frame, text="ITENS PARA LOOT", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        canvas = ctk.CTkScrollableFrame(frame, fg_color="transparent", corner_radius=0)
        canvas.grid(row=1, column=0, sticky="nsew", padx=6, pady=(0, 2))
        canvas.grid_columnconfigure(0, weight=1)
        self._items_canvas = canvas

        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(4, 10))
        btn_frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkButton(btn_frame, text="+ Add preset", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      text_color="white", command=self._add_preset).grid(
            row=0, column=0, padx=1, sticky="ew")
        ctk.CTkButton(btn_frame, text="- Remover", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color="#c0392b", hover_color="#96281b",
                      text_color="white", command=self._remove_item).grid(
            row=0, column=1, padx=1, sticky="ew")
        ctk.CTkButton(btn_frame, text="Limpar cache", font=FONTS["small"],
                      height=28, corner_radius=6,
                      fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
                      text_color=COLORS["text_label"],
                      command=self._clear_cache).grid(
            row=0, column=2, padx=1, sticky="ew")

        self._refresh_items()

    def _build_status(self, parent):
        frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"], corner_radius=12,
                             border_width=1, border_color=COLORS["border"])
        frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=0, pady=(6, 0))
        frame.grid_columnconfigure((0, 1, 2), weight=1)

        ctk.CTkLabel(frame, text="ESTATISTICAS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=3, padx=12, pady=(8, 4), sticky="w")

        self._var_looted = ctk.StringVar(value="0")
        self._var_pending = ctk.StringVar(value="0")
        self._var_tracked = ctk.StringVar(value="0")

        for i, (lbl, var) in enumerate([
            ("Corpses saqueados", self._var_looted),
            ("Kills pendentes", self._var_pending),
            ("Itens trackeados", self._var_tracked),
        ]):
            ctk.CTkLabel(frame, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=1, column=i, padx=12, pady=(0, 1), sticky="w")
            ctk.CTkLabel(frame, textvariable=var, font=("Segoe UI", 16, "bold"),
                         text_color=COLORS["accent_light"]).grid(
                row=2, column=i, padx=12, pady=(0, 10), sticky="w")

    def _load_items(self):
        script = self._get_script()
        if script is None:
            return list(_ITEMS_PRESET)
        items = script.config.get("items_to_loot", {})
        if not items:
            return list(_ITEMS_PRESET)
        return [(int(k), v) for k, v in items.items()]

    def _sync_items(self):
        script = self._get_script()
        if script is None:
            return
        items = {}
        for child in self._items_canvas.winfo_children():
            if hasattr(child, "_item_id"):
                items[child._item_id] = child._item_name
        script.config["items_to_loot"] = items
        self._schedule_save()

    def _refresh_items(self):
        for w in self._items_canvas.winfo_children():
            w.destroy()
        items = self._load_items()
        for item_id, item_name in items:
            row = ctk.CTkFrame(self._items_canvas, fg_color="transparent")
            row.grid(sticky="ew", pady=1)
            row.grid_columnconfigure(1, weight=1)
            row._item_id = item_id
            row._item_name = item_name
            ctk.CTkLabel(row, text=f"[{item_id}]", font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=0, column=0, padx=(6, 2), pady=3, sticky="w")
            ctk.CTkLabel(row, text=item_name, font=FONTS["body"],
                         text_color=COLORS["text_label"]).grid(
                row=0, column=1, padx=(0, 6), sticky="w")

    def _add_preset(self):
        script = self._get_script()
        items = script.config.get("items_to_loot", {}) if script else {}
        for item_id, item_name in _ITEMS_PRESET:
            items[item_id] = item_name
        if script:
            script.config["items_to_loot"] = items
            self._schedule_save()
        self._refresh_items()

    def _remove_item(self):
        script = self._get_script()
        if script is None:
            return
        items = script.config.get("items_to_loot", {})
        if items:
            last_key = list(items.keys())[-1]
            del items[last_key]
            self._schedule_save()
        self._refresh_items()

    def _clear_cache(self):
        script = self._get_script()
        if script:
            script.clear_looted_cache()
            self.app.log("Cache de loot limpo.", COLORS["accent_light"])
