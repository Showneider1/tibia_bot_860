"""
Aba de Cavebot - waypoints e configuracoes de hunt conectados ao CavebotScript.

Formas de adicionar waypoint (estilo ElfBot/WindBot):
    1. Posicao atual: botoes que pegam a posicao do player no momento
       com offset direcional (mesmo SQM, Norte, Sul, Leste, Oeste, diagonais)
    2. Manual: campos X/Y/Z/Acao para digitar a posicao desejada

Funcionalidades:
    - Salvar waypoints em arquivo .json
    - Carregar waypoints de arquivo .json
    - Switches de opcoes aplicados em tempo real ao CavebotScript

Formato do arquivo de waypoints salvo:
    [
      {"x": 1000, "y": 2000, "z": 7, "action": "walk"},
      ...
    ]
"""
import json
import os
import customtkinter as ctk
from tkinter import filedialog
from src.ui.theme import COLORS, FONTS
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position

# Pasta padrao onde os perfis de waypoint sao salvos
DEFAULT_WP_DIR = os.path.join(os.path.expanduser("~"), "tibia_bot_waypoints")

# Offsets direcionais exatamente como ElfBot/WindBot
# (dx, dy)  -- no Tibia: Y sobe indo para Norte (Y-1)
DIRECTIONS = [
    ("NW",   -1, -1), ("N",   0, -1), ("NE",  +1, -1),
    ("W",    -1,  0), ("Aqui", 0,  0), ("E",  +1,  0),
    ("SW",   -1, +1), ("S",   0, +1), ("SE",  +1, +1),
]


class CavebotTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # variaveis da aba manual
        self._var_x      = ctk.StringVar(value="")
        self._var_y      = ctk.StringVar(value="")
        self._var_z      = ctk.StringVar(value="7")
        self._var_action = ctk.StringVar(value="walk")

        # label de posicao atual
        self._var_pos_label  = ctk.StringVar(value="Posicao atual: desconhecida")
        self._var_action_pos = ctk.StringVar(value="walk")

        # nome do perfil carregado
        self._var_profile = ctk.StringVar(value="sem perfil")

        # referencias
        self._opt_vars: dict = {}
        self._wp_scroll = None

        os.makedirs(DEFAULT_WP_DIR, exist_ok=True)
        self._build()

        # atualiza posicao a cada 1s
        self._update_pos_label()

    # ------------------------------------------------------------------
    # Acesso ao engine
    # ------------------------------------------------------------------

    def _get_script(self):
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        se = getattr(engine, "script_engine", None)
        if se is not None:
            for s in getattr(se, "_scripts", []):
                if getattr(s, "name", "") in ("CaveBot", "cavebot", "Cavebot"):
                    return s
        scripts = getattr(engine, "scripts", None) or getattr(engine, "_scripts", None)
        if scripts is None:
            return None
        if isinstance(scripts, dict):
            return scripts.get("CaveBot") or scripts.get("cavebot")
        for s in scripts:
            if getattr(s, "name", "") in ("CaveBot", "cavebot", "Cavebot"):
                return s
        return None

    def _get_player_pos(self):
        """Retorna Position atual do player, ou None."""
        try:
            engine = getattr(self.app, "bot_engine", None)
            if engine is None:
                return None
            player = getattr(engine, "player", None) or getattr(engine, "_player", None)
            if player is None:
                return None
            pos = getattr(player, "position", None)
            if pos and pos.x > 0 and pos.y > 0:
                return pos
        except Exception:
            pass
        return None

    def _update_pos_label(self):
        """Atualiza o label com a posicao atual do player a cada 1s."""
        pos = self._get_player_pos()
        if pos:
            self._var_pos_label.set(f"Posicao atual:  X={pos.x}  Y={pos.y}  Z={pos.z}")
        else:
            self._var_pos_label.set("Posicao atual: aguardando conexao...")
        self.after(1000, self._update_pos_label)

    def _apply_bool(self, cfg_key, var):
        script = self._get_script()
        if script:
            script.config[cfg_key] = var.get()

    # ------------------------------------------------------------------
    # Adicionar waypoint - FORMA 1: posicao atual + direcao
    # ------------------------------------------------------------------

    def _add_by_position(self, dx: int, dy: int) -> None:
        """Pega a posicao atual do player, aplica offset e adiciona waypoint."""
        pos = self._get_player_pos()
        if pos is None:
            self.app.log(
                "Cavebot: nao foi possivel obter a posicao atual. Bot conectado?",
                COLORS["warn_yellow"],
            )
            return

        x = pos.x + dx
        y = pos.y + dy
        z = pos.z
        action = self._var_action_pos.get().strip() or "walk"

        self._do_add(x, y, z, action)

    # ------------------------------------------------------------------
    # Adicionar waypoint - FORMA 2: entrada manual
    # ------------------------------------------------------------------

    def _add_manual(self) -> None:
        x_raw = self._var_x.get().strip()
        y_raw = self._var_y.get().strip()
        z_raw = self._var_z.get().strip()

        if not x_raw or not y_raw or not z_raw:
            self.app.log("Cavebot: preencha X, Y e Z antes de adicionar.", COLORS["warn_yellow"])
            return

        try:
            x, y, z = int(x_raw), int(y_raw), int(z_raw)
        except ValueError:
            self.app.log("Cavebot: X, Y e Z precisam ser numeros inteiros.", COLORS["warn_yellow"])
            return

        action = self._var_action.get().strip() or "walk"
        self._do_add(x, y, z, action)
        self._var_x.set("")
        self._var_y.set("")

    # ------------------------------------------------------------------
    # Core: efetivamente insere o waypoint
    # ------------------------------------------------------------------

    def _do_add(self, x: int, y: int, z: int, action: str) -> None:
        wp = Waypoint(position=Position(x=x, y=y, z=z), action=action)
        script = self._get_script()
        if script:
            script.add_waypoint(wp)
            self.app.log(f"Waypoint adicionado: ({x}, {y}, {z}) [{action}]", COLORS["online_green"])
        else:
            self._demo_waypoints = getattr(self, "_demo_waypoints", [])
            self._demo_waypoints.append(wp)
            self.app.log(f"[DEMO] Waypoint ({x}, {y}, {z}) [{action}] registrado.", COLORS["text_faint"])
        self._refresh_waypoints()

    # ------------------------------------------------------------------
    # Limpar
    # ------------------------------------------------------------------

    def _clear_waypoints(self) -> None:
        script = self._get_script()
        if script:
            script.clear_waypoints()
        if hasattr(self, "_demo_waypoints"):
            self._demo_waypoints.clear()
        self._var_profile.set("sem perfil")
        self.app.log("Waypoints removidos.", COLORS["warn_yellow"])
        self._refresh_waypoints()

    def _get_current_waypoints(self) -> list:
        script = self._get_script()
        if script:
            return script.config.get("waypoints", [])
        return getattr(self, "_demo_waypoints", [])

    # ------------------------------------------------------------------
    # Save / Load  (estilo ElfBot/WindBot)
    # ------------------------------------------------------------------

    def _save_waypoints(self) -> None:
        waypoints = self._get_current_waypoints()
        if not waypoints:
            self.app.log("Cavebot: nenhum waypoint para salvar.", COLORS["warn_yellow"])
            return
        filepath = filedialog.asksaveasfilename(
            initialdir=DEFAULT_WP_DIR, title="Salvar waypoints",
            defaultextension=".json",
            filetypes=[("Waypoint JSON", "*.json"), ("Todos", "*.*")],
        )
        if not filepath:
            return
        data = [
            {"x": wp.position.x, "y": wp.position.y,
             "z": wp.position.z, "action": wp.action}
            for wp in waypoints
        ]
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            name = os.path.splitext(os.path.basename(filepath))[0]
            self._var_profile.set(name)
            self.app.log(f"Waypoints salvos: '{name}' ({len(data)} pontos)", COLORS["online_green"])
        except Exception as e:
            self.app.log(f"Erro ao salvar waypoints: {e}", COLORS["hp_red"])

    def _load_waypoints(self) -> None:
        filepath = filedialog.askopenfilename(
            initialdir=DEFAULT_WP_DIR, title="Carregar waypoints",
            filetypes=[("Waypoint JSON", "*.json"), ("Todos", "*.*")],
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.app.log(f"Erro ao abrir arquivo: {e}", COLORS["hp_red"])
            return
        if not isinstance(data, list):
            self.app.log("Arquivo invalido: esperado uma lista de waypoints.", COLORS["hp_red"])
            return
        script = self._get_script()
        if script:
            script.clear_waypoints()
        if hasattr(self, "_demo_waypoints"):
            self._demo_waypoints.clear()
        loaded = errors = 0
        for item in data:
            try:
                wp = Waypoint(
                    position=Position(x=int(item["x"]), y=int(item["y"]), z=int(item["z"])),
                    action=str(item.get("action", "walk")),
                )
                if script:
                    script.add_waypoint(wp)
                else:
                    self._demo_waypoints = getattr(self, "_demo_waypoints", [])
                    self._demo_waypoints.append(wp)
                loaded += 1
            except (KeyError, ValueError, TypeError):
                errors += 1
        name = os.path.splitext(os.path.basename(filepath))[0]
        self._var_profile.set(name)
        msg = f"Perfil '{name}' carregado: {loaded} waypoints"
        if errors:
            msg += f" ({errors} erro(s) ignorados)"
        self.app.log(msg, COLORS["online_green"])
        self._refresh_waypoints()

    # ------------------------------------------------------------------
    # Refresh da lista
    # ------------------------------------------------------------------

    def _refresh_waypoints(self) -> None:
        if self._wp_scroll is None:
            return
        for w in self._wp_scroll.winfo_children():
            w.destroy()
        waypoints = self._get_current_waypoints()
        widths = [30, 70, 70, 40, 80]
        if not waypoints:
            ctk.CTkLabel(
                self._wp_scroll, text="Nenhum waypoint cadastrado.",
                font=FONTS["small"], text_color=COLORS["text_faint"],
            ).pack(pady=16)
            return
        for idx, wp in enumerate(waypoints, start=1):
            p    = wp.position
            vals = (str(idx), str(p.x), str(p.y), str(p.z), wp.action)
            row  = ctk.CTkFrame(self._wp_scroll, fg_color=COLORS["bg_panel"], corner_radius=8)
            row.pack(fill="x", pady=3)
            for j, (val, w) in enumerate(zip(vals, widths)):
                color = COLORS["accent_light"] if j == 0 else COLORS["text_muted"]
                ctk.CTkLabel(
                    row, text=val, font=FONTS["body"],
                    text_color=color, width=w,
                ).pack(side="left", padx=6, pady=8)

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
        card.grid_rowconfigure(6, weight=1)

        # ---- Header toolbar ----
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.grid(row=0, column=0, padx=16, pady=(14, 4), sticky="ew")
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="WAYPOINTS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(row=0, column=0, sticky="w")
        btn_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_frame.grid(row=0, column=1)
        ctk.CTkButton(
            btn_frame, text="Limpar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["hp_red"], hover_color="#c04040",
            command=self._clear_waypoints,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            btn_frame, text="↺", font=FONTS["small"], height=28, width=36,
            corner_radius=8, fg_color=COLORS["bg_panel"],
            hover_color=COLORS["bg_hover"], text_color=COLORS["text_label"],
            command=self._refresh_waypoints,
        ).pack(side="left", padx=3)

        # ---- Save / Load ----
        io_bar = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=8)
        io_bar.grid(row=1, column=0, padx=12, pady=(0, 6), sticky="ew")
        io_bar.grid_columnconfigure(2, weight=1)
        ctk.CTkButton(
            io_bar, text="💾  Salvar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._save_waypoints,
        ).grid(row=0, column=0, padx=(8, 4), pady=6)
        ctk.CTkButton(
            io_bar, text="📂  Carregar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_label"], border_width=1, border_color=COLORS["border"],
            command=self._load_waypoints,
        ).grid(row=0, column=1, padx=(0, 8), pady=6)
        ctk.CTkLabel(
            io_bar, textvariable=self._var_profile,
            font=FONTS["small"], text_color=COLORS["text_faint"],
        ).grid(row=0, column=2, padx=(0, 12), pady=6, sticky="e")

        # ==================================================================
        # FORMA 1: Posicao Atual  (estilo ElfBot/WindBot)
        # ==================================================================
        sec1 = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=10)
        sec1.grid(row=2, column=0, padx=12, pady=(0, 6), sticky="ew")
        sec1.grid_columnconfigure(0, weight=1)

        # Header da secao
        hdr1 = ctk.CTkFrame(sec1, fg_color="transparent")
        hdr1.grid(row=0, column=0, padx=8, pady=(8, 2), sticky="ew")
        hdr1.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            hdr1, text="Posicao Atual", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).grid(row=0, column=0, sticky="w")
        # Label de coordenadas ao vivo
        ctk.CTkLabel(
            hdr1, textvariable=self._var_pos_label,
            font=FONTS["small"], text_color=COLORS["text_faint"],
        ).grid(row=0, column=1, sticky="e", padx=(8, 0))

        # Grid de direcoes 3x3 (NW/N/NE / W/Aqui/E / SW/S/SE)
        dir_grid = ctk.CTkFrame(sec1, fg_color="transparent")
        dir_grid.grid(row=1, column=0, padx=8, pady=(4, 4))

        for i, (label, dx, dy) in enumerate(DIRECTIONS):
            row_i = i // 3
            col_i = i % 3
            is_center = (label == "Aqui")
            ctk.CTkButton(
                dir_grid,
                text=label,
                width=56, height=34,
                font=FONTS["small"],
                corner_radius=8,
                fg_color=COLORS["accent"] if is_center else COLORS["bg_input"],
                hover_color=COLORS["accent_hover"] if is_center else COLORS["bg_hover"],
                text_color=COLORS["text_primary"] if is_center else COLORS["text_label"],
                border_width=0 if is_center else 1,
                border_color=COLORS["border"],
                command=lambda dx=dx, dy=dy: self._add_by_position(dx, dy),
            ).grid(row=row_i, column=col_i, padx=3, pady=3)

        # Acao para o modo posicao atual
        act_row1 = ctk.CTkFrame(sec1, fg_color="transparent")
        act_row1.grid(row=2, column=0, padx=8, pady=(0, 8), sticky="w")
        ctk.CTkLabel(
            act_row1, text="Acao:", font=FONTS["badge"],
            text_color=COLORS["text_faint"],
        ).pack(side="left", padx=(0, 6))
        ctk.CTkComboBox(
            act_row1,
            values=["walk", "rope", "shovel", "ladder", "teleport", "home", "refill"],
            variable=self._var_action_pos,
            width=140, height=28, font=FONTS["body"],
            fg_color=COLORS["bg_input"], border_color=COLORS["border"],
            text_color=COLORS["text_label"], button_color=COLORS["accent"],
            dropdown_fg_color=COLORS["bg_card"],
        ).pack(side="left")

        # ==================================================================
        # FORMA 2: Entrada Manual
        # ==================================================================
        sec2 = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=10)
        sec2.grid(row=3, column=0, padx=12, pady=(0, 6), sticky="ew")

        ctk.CTkLabel(
            sec2, text="Entrada Manual", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).pack(anchor="w", padx=10, pady=(8, 4))

        manual_row = ctk.CTkFrame(sec2, fg_color="transparent")
        manual_row.pack(fill="x", padx=8, pady=(0, 8))
        for label, var, w in [
            ("X", self._var_x, 76),
            ("Y", self._var_y, 76),
            ("Z", self._var_z, 48),
            ("Acao", self._var_action, 100),
        ]:
            ctk.CTkLabel(
                manual_row, text=label, font=FONTS["badge"],
                text_color=COLORS["text_faint"], width=24,
            ).pack(side="left", padx=(8, 2))
            ctk.CTkEntry(
                manual_row, textvariable=var, height=28, width=w, corner_radius=6,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            ).pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            manual_row, text="+ Adicionar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._add_manual,
        ).pack(side="left", padx=(8, 0))

        # ---- Cabecalho da tabela ----
        headers = ["#", "X", "Y", "Z", "Acao"]
        widths  = [30, 70, 70, 40, 80]
        col_frame = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=6)
        col_frame.grid(row=4, column=0, padx=12, pady=(0, 4), sticky="ew")
        for h, w in zip(headers, widths):
            ctk.CTkLabel(
                col_frame, text=h, font=FONTS["badge"],
                text_color=COLORS["text_faint"], width=w,
            ).pack(side="left", padx=6, pady=6)

        # ---- Scroll de waypoints ----
        self._wp_scroll = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        self._wp_scroll.grid(row=6, column=0, padx=12, pady=(0, 12), sticky="nsew")
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
            ("Lootar criaturas",  "loop",                      True),
            ("Atacar automatico", "use_pathfinding",           True),
            ("Anti-stuck",        "enable_anti_stuck",         True),
            ("Pausar se atacado", "pause_follow_in_combat",    False),
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
            card, values=["Menor HP", "Mais proximo", "Mais longe", "Mais forte"],
            variable=self._var_target_mode,
            font=FONTS["body"], fg_color=COLORS["bg_input"],
            border_color=COLORS["border"], text_color=COLORS["text_label"],
            button_color=COLORS["accent"], dropdown_fg_color=COLORS["bg_card"],
        ).grid(row=11, column=0, padx=16, pady=(0, 16), sticky="ew")

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
