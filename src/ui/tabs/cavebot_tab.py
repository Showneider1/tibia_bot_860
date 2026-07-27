"""
Aba de Cavebot - waypoints e configuracoes de hunt conectados ao CavebotScript.

Conexao com o script:
    - Botao '+ Adicionar' cria Waypoint e chama script.add_waypoint()
    - Botao 'Limpar'      chama script.clear_waypoints()
    - Switches chamam _apply_bool() para atualizar config em tempo real
    - Lista de waypoints e recarregada via _refresh_waypoints()
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position


class CavebotTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # variaveis dos campos de adicionar waypoint
        self._var_x      = ctk.StringVar()
        self._var_y      = ctk.StringVar()
        self._var_z      = ctk.StringVar(value="7")
        self._var_action = ctk.StringVar(value="walk")

        # referencias aos switches de opcoes
        self._opt_vars: dict = {}

        # referencia ao frame scrollavel de waypoints
        self._wp_scroll = None

        self._build()

    # ------------------------------------------------------------------
    # Acesso ao CavebotScript via BotEngine
    # ------------------------------------------------------------------

    def _get_script(self):
        """Retorna a instancia de CavebotScript do engine, ou None."""
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        scripts = getattr(engine, "scripts", None) or getattr(engine, "_scripts", None)
        if scripts is None:
            return None
        if isinstance(scripts, dict):
            return scripts.get("CaveBot") or scripts.get("cavebot")
        for s in scripts:
            if getattr(s, "name", "") in ("CaveBot", "cavebot"):
                return s
        return None

    def _apply_bool(self, cfg_key: str, var: ctk.BooleanVar) -> None:
        script = self._get_script()
        if script:
            script.config[cfg_key] = var.get()

    # ------------------------------------------------------------------
    # Acoes de waypoint
    # ------------------------------------------------------------------

    def _add_waypoint(self) -> None:
        """Le os campos X/Y/Z/Acao e adiciona waypoint ao script."""
        try:
            x = int(self._var_x.get())
            y = int(self._var_y.get())
            z = int(self._var_z.get())
        except ValueError:
            self.app.log("Cavebot: X, Y e Z precisam ser inteiros.", COLORS["warn_yellow"])
            return

        action = self._var_action.get().strip() or "walk"
        wp     = Waypoint(position=Position(x=x, y=y, z=z), action=action)

        script = self._get_script()
        if script:
            script.add_waypoint(wp)
            self.app.log(f"Waypoint adicionado: ({x}, {y}, {z}) [{action}]", COLORS["online_green"])
        else:
            self.app.log("[DEMO] Waypoint registrado localmente (sem engine).", COLORS["text_faint"])

        self._var_x.set("")
        self._var_y.set("")
        self._refresh_waypoints()

    def _clear_waypoints(self) -> None:
        """Remove todos os waypoints do script."""
        script = self._get_script()
        if script:
            script.clear_waypoints()
            self.app.log("Waypoints removidos.", COLORS["warn_yellow"])
        self._refresh_waypoints()

    def _refresh_waypoints(self) -> None:
        """Atualiza a lista de waypoints exibida na UI."""
        if self._wp_scroll is None:
            return

        for w in self._wp_scroll.winfo_children():
            w.destroy()

        script    = self._get_script()
        waypoints = script.config.get("waypoints", []) if script else []

        widths = [30, 70, 70, 40, 80]

        if not waypoints:
            ctk.CTkLabel(
                self._wp_scroll,
                text="Nenhum waypoint cadastrado.",
                font=FONTS["small"],
                text_color=COLORS["text_faint"],
            ).pack(pady=16)
            return

        for idx, wp in enumerate(waypoints, start=1):
            p    = wp.position
            vals = (str(idx), str(p.x), str(p.y), str(p.z), wp.action)
            row  = ctk.CTkFrame(self._wp_scroll, fg_color=COLORS["bg_panel"], corner_radius=8)
            row.pack(fill="x", pady=3)
            for j, (val, w) in enumerate(zip(vals, widths)):
                color = COLORS["accent_light"] if j == 0 else COLORS["text_muted"]
                ctk.CTkLabel(row, text=val, font=FONTS["body"],
                             text_color=color, width=w).pack(side="left", padx=6, pady=8)

    # ------------------------------------------------------------------
    # Construcao da UI
    # ------------------------------------------------------------------

    def _build(self):
        ctk.CTkLabel(self, text="Cavebot", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(self, text="Gerencie waypoints e comportamento do bot em cave",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        self._waypoint_panel()
        self._config_panel()

    def _waypoint_panel(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=0, padx=(24, 8), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)
        card.grid_rowconfigure(3, weight=1)

        # --- Header com botoes ---
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(14, 8), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="WAYPOINTS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(row=0, column=0, sticky="w")

        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        ctk.CTkButton(
            btn_frame, text="+ Adicionar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._add_waypoint,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_frame, text="Limpar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["hp_red"],
            hover_color="#c04040",
            command=self._clear_waypoints,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_frame, text="Atualizar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["bg_panel"],
            hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_label"],
            command=self._refresh_waypoints,
        ).pack(side="left", padx=4)

        # --- Linha de adicao rapida ---
        add_row = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=8)
        add_row.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        for label, var, w in [
            ("X", self._var_x, 80),
            ("Y", self._var_y, 80),
            ("Z", self._var_z, 50),
            ("Acao", self._var_action, 100),
        ]:
            ctk.CTkLabel(add_row, text=label, font=FONTS["badge"],
                         text_color=COLORS["text_faint"], width=24).pack(side="left", padx=(8, 2), pady=6)
            ctk.CTkEntry(
                add_row, textvariable=var, height=28, width=w, corner_radius=6,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            ).pack(side="left", padx=(0, 6), pady=6)

        # --- Cabecalho da tabela ---
        headers = ["#", "X", "Y", "Z", "Acao"]
        widths  = [30, 70, 70, 40, 80]
        col_frame = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=6)
        col_frame.grid(row=2, column=0, padx=12, pady=(0, 4), sticky="ew")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(col_frame, text=h, font=FONTS["badge"],
                         text_color=COLORS["text_faint"], width=w).pack(side="left", padx=6, pady=6)

        # --- Scroll de waypoints ---
        self._wp_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        self._wp_scroll.grid(row=3, column=0, padx=12, pady=(0, 12), sticky="nsew")
        self._refresh_waypoints()

    def _config_panel(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=1, padx=(0, 24), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="OPCOES", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=16, pady=(14, 8), sticky="w")

        opts = [
            ("Lootar criaturas",  "loop",                    True),
            ("Atacar automatico", "use_pathfinding",         True),
            ("Anti-stuck",        "enable_anti_stuck",       True),
            ("Pausar se atacado", "pause_follow_in_combat",  False),
            ("Desviar perigosos", "avoid_dangerous_creatures", False),
        ]
        for i, (lbl, cfg_key, default) in enumerate(opts):
            var = ctk.BooleanVar(value=default)
            self._opt_vars[cfg_key] = var
            ctk.CTkSwitch(
                card, text=lbl, variable=var,
                font=FONTS["body"], text_color=COLORS["text_label"],
                progress_color=COLORS["accent"],
                command=lambda k=cfg_key, v=var: self._apply_bool(k, v),
            ).grid(row=i + 1, column=0, padx=16, pady=6, sticky="w")

        ctk.CTkLabel(card, text="Modo de alvo", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=10, column=0, padx=16, pady=(16, 4), sticky="w")
        self._var_target_mode = ctk.StringVar(value="Mais proximo")
        ctk.CTkComboBox(
            card,
            values=["Menor HP", "Mais proximo", "Mais longe", "Mais forte"],
            variable=self._var_target_mode,
            font=FONTS["body"],
            fg_color=COLORS["bg_input"],
            border_color=COLORS["border"],
            text_color=COLORS["text_label"],
            button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
        ).grid(row=11, column=0, padx=16, pady=(0, 16), sticky="ew")

        # Timeout anti-stuck
        ctk.CTkLabel(card, text="Timeout stuck (s)", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=12, column=0, padx=16, pady=(8, 4), sticky="w")
        self._var_stuck_timeout = ctk.StringVar(value="8")
        stuck_e = ctk.CTkEntry(
            card, textvariable=self._var_stuck_timeout, height=32, corner_radius=8,
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_label"], font=FONTS["body"],
        )
        stuck_e.grid(row=13, column=0, padx=16, pady=(0, 16), sticky="ew")
        stuck_e.bind("<FocusOut>", lambda e: self._apply_timeout())
        stuck_e.bind("<Return>",   lambda e: self._apply_timeout())

    def _apply_timeout(self) -> None:
        script = self._get_script()
        if script is None:
            return
        try:
            script.config["stuck_timeout"] = float(self._var_stuck_timeout.get())
        except ValueError:
            pass
