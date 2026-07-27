"""
Aba de Cavebot redesenhada.

Funcionalidades:
  - Botao ATIVAR / DESATIVAR cavebot (faz o boneco andar)
  - Secoes de hunt (estilo WindBot): cada secao tem nome proprio,
    pode ser ativada/desativada e possui sua propria lista de waypoints
  - Tipos de waypoint: Walk, Node, Stand, Rope, Shovel, Ladder, Use, Lure, Action
  - Grid direcional 3x3 para capturar posicao atual
  - Entrada manual X / Y / Z
  - Salvar / Carregar perfis .json

Formato do arquivo .json:
  {
    "sections": [
      {
        "name": "Descida",
        "enabled": true,
        "waypoints": [
          {"x": 1000, "y": 2000, "z": 7, "action": "walk"}, ...
        ]
      }, ...
    ]
  }
"""
import json
import os
import customtkinter as ctk
from tkinter import filedialog, simpledialog
from src.ui.theme import COLORS, FONTS
from src.core.entities.waypoint import Waypoint
from src.core.value_objects.position import Position

DEFAULT_WP_DIR = os.path.join(os.path.expanduser("~"), "tibia_bot_waypoints")

DIRECTIONS = [
    ("NW", -1, -1), ("N",    0, -1), ("NE", +1, -1),
    ("W",  -1,  0), ("Aqui", 0,  0), ("E",  +1,  0),
    ("SW", -1, +1), ("S",    0, +1), ("SE", +1, +1),
]

WP_TYPES = ["Walk", "Node", "Stand", "Rope", "Shovel", "Ladder", "Use", "Lure", "Action"]

WP_TYPE_COLORS = {
    "Walk":   "#3a7ebf",
    "Node":   "#4a9e6b",
    "Stand":  "#7a5cbf",
    "Rope":   "#bf8c3a",
    "Shovel": "#bf6a3a",
    "Ladder": "#bf5a5a",
    "Use":    "#3abfbf",
    "Lure":   "#bf3a7e",
    "Action": "#6abf3a",
}


class _Section:
    """Representa uma secao de hunt com nome, estado e lista de waypoints."""
    def __init__(self, name: str, enabled: bool = True):
        self.name = name
        self.enabled = enabled
        self.waypoints: list = []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "enabled": self.enabled,
            "waypoints": [
                {"x": wp.position.x, "y": wp.position.y,
                 "z": wp.position.z, "action": wp.action}
                for wp in self.waypoints
            ],
        }

    @staticmethod
    def from_dict(d: dict) -> "_Section":
        s = _Section(d.get("name", "Secao"), d.get("enabled", True))
        for item in d.get("waypoints", []):
            try:
                s.waypoints.append(Waypoint(
                    position=Position(x=int(item["x"]), y=int(item["y"]), z=int(item["z"])),
                    action=str(item.get("action", "walk")),
                ))
            except (KeyError, ValueError, TypeError):
                pass
        return s


class CavebotTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app

        self._active = False
        self._sections: list[_Section] = [_Section("Secao 1")]
        self._current_section_idx = 0
        self._selected_wp_idx: int | None = None
        self._selected_type = ctk.StringVar(value="Walk")
        self._var_profile = ctk.StringVar(value="sem perfil")
        self._var_pos_label = ctk.StringVar(value="aguardando conexao...")
        self._var_x = ctk.StringVar(value="")
        self._var_y = ctk.StringVar(value="")
        self._var_z = ctk.StringVar(value="7")
        self._opt_vars: dict = {}

        self._btn_activate: ctk.CTkButton | None = None
        self._section_list_frame: ctk.CTkFrame | None = None
        self._wp_scroll: ctk.CTkScrollableFrame | None = None
        self._type_buttons: dict = {}

        os.makedirs(DEFAULT_WP_DIR, exist_ok=True)
        self._build()
        self._update_pos_label()

    # ------------------------------------------------------------------
    # Helpers: engine / script / player
    # ------------------------------------------------------------------

    def _get_script(self):
        """Retorna o CavebotScript registrado no script_engine, ou None."""
        engine = getattr(self.app, "bot_engine", None)
        if engine is None:
            return None
        return engine.script_engine.get_script("CaveBot")

    def _get_player_pos(self):
        try:
            engine = getattr(self.app, "bot_engine", None)
            if engine is None:
                return None
            pos = getattr(getattr(engine, "player", None), "position", None)
            if pos and pos.x > 0 and pos.y > 0:
                return pos
        except Exception:
            pass
        return None

    def _update_pos_label(self):
        pos = self._get_player_pos()
        if pos:
            self._var_pos_label.set(f"X={pos.x}  Y={pos.y}  Z={pos.z}")
        else:
            self._var_pos_label.set("aguardando conexao...")
        self.after(1000, self._update_pos_label)

    # ------------------------------------------------------------------
    # Ativar / Desativar
    # ------------------------------------------------------------------

    def _sync_waypoints_to_script(self, script) -> int:
        """Limpa waypoints do script e recarrega de todas as secoes habilitadas."""
        script.clear_waypoints()
        total = 0
        for sec in self._sections:
            if sec.enabled:
                for wp in sec.waypoints:
                    script.add_waypoint(wp)
                    total += 1
        return total

    def _toggle_active(self):
        self._active = not self._active

        script = self._get_script()
        engine = getattr(self.app, "bot_engine", None)

        if self._active:
            total_wps = 0
            if script:
                total_wps = self._sync_waypoints_to_script(script)
                script.enabled = True
                script.on_enable()
            if engine:
                engine.enabled = True
            state_msg = f"Cavebot ATIVADO ({total_wps} waypoints carregados)."
            color = COLORS["online_green"]
        else:
            if script:
                script.enabled = False
                script.on_disable()
            # Desativa engine somente se nenhum outro script estiver ativo
            if engine:
                other_active = any(
                    getattr(s, "enabled", False)
                    for s in engine.script_engine._scripts
                    if s.name != "CaveBot"
                )
                if not other_active:
                    engine.enabled = False
            state_msg = "Cavebot desativado."
            color = COLORS["warn_yellow"]

        self._refresh_activate_btn()
        self.app.log(state_msg, color)

    def _refresh_activate_btn(self):
        if self._btn_activate is None:
            return
        if self._active:
            self._btn_activate.configure(
                text="\u23f9  Desativar Cavebot",
                fg_color=COLORS["hp_red"],
                hover_color="#c04040",
            )
        else:
            self._btn_activate.configure(
                text="\u25b6  Ativar Cavebot",
                fg_color=COLORS["online_green"],
                hover_color="#2e7d32",
            )

    # ------------------------------------------------------------------
    # Secoes
    # ------------------------------------------------------------------

    @property
    def _section(self) -> _Section:
        idx = self._current_section_idx
        if 0 <= idx < len(self._sections):
            return self._sections[idx]
        return self._sections[0]

    def _add_section(self):
        name = simpledialog.askstring(
            "Nova Secao", "Nome da secao:",
            initialvalue=f"Secao {len(self._sections) + 1}",
        )
        if not name:
            return
        self._sections.append(_Section(name.strip()))
        self._current_section_idx = len(self._sections) - 1
        self._refresh_section_list()
        self._refresh_waypoints()
        self.app.log(f"Secao '{name}' criada.", COLORS["accent_light"])

    def _remove_section(self):
        if len(self._sections) <= 1:
            self.app.log("Precisa ter ao menos uma secao.", COLORS["warn_yellow"])
            return
        name = self._section.name
        self._sections.pop(self._current_section_idx)
        self._current_section_idx = max(0, self._current_section_idx - 1)
        self._refresh_section_list()
        self._refresh_waypoints()
        self.app.log(f"Secao '{name}' removida.", COLORS["warn_yellow"])

    def _rename_section(self):
        name = simpledialog.askstring(
            "Renomear", "Novo nome:",
            initialvalue=self._section.name,
        )
        if not name:
            return
        self._section.name = name.strip()
        self._refresh_section_list()

    def _select_section(self, idx: int):
        self._current_section_idx = idx
        self._selected_wp_idx = None
        self._refresh_section_list()
        self._refresh_waypoints()

    def _toggle_section_enabled(self, idx: int):
        self._sections[idx].enabled = not self._sections[idx].enabled
        self._refresh_section_list()
        if self._active:
            script = self._get_script()
            if script:
                total = self._sync_waypoints_to_script(script)
                sec = self._sections[idx]
                status = "habilitada" if sec.enabled else "desabilitada"
                self.app.log(
                    f"Secao '{sec.name}' {status} — {total} waypoints ativos.",
                    COLORS["accent_light"],
                )

    def _refresh_section_list(self):
        if self._section_list_frame is None:
            return
        for w in self._section_list_frame.winfo_children():
            w.destroy()
        for i, sec in enumerate(self._sections):
            is_sel = (i == self._current_section_idx)
            row_bg = COLORS["accent"] if is_sel else COLORS["bg_panel"]
            row = ctk.CTkFrame(
                self._section_list_frame,
                fg_color=row_bg, corner_radius=8,
            )
            row.pack(fill="x", padx=4, pady=2)
            row.grid_columnconfigure(1, weight=1)

            status_color = COLORS["online_green"] if sec.enabled else COLORS["hp_red"]
            dot = ctk.CTkButton(
                row, text="\u25cf", width=22, height=22, corner_radius=11,
                fg_color="transparent", hover_color=row_bg,
                text_color=status_color, font=("Segoe UI", 10),
                command=lambda idx=i: self._toggle_section_enabled(idx),
            )
            dot.grid(row=0, column=0, padx=(6, 2), pady=4)

            name_lbl = ctk.CTkLabel(
                row, text=sec.name,
                font=FONTS["body"],
                text_color=COLORS["text_primary"] if is_sel else COLORS["text_label"],
                anchor="w",
            )
            name_lbl.grid(row=0, column=1, sticky="ew", padx=4)
            name_lbl.bind("<Button-1>", lambda e, idx=i: self._select_section(idx))
            row.bind("<Button-1>",      lambda e, idx=i: self._select_section(idx))

            cnt_lbl = ctk.CTkLabel(
                row, text=str(len(sec.waypoints)),
                font=FONTS["small"],
                text_color=COLORS["text_faint"], width=24,
            )
            cnt_lbl.grid(row=0, column=2, padx=(0, 6))

    # ------------------------------------------------------------------
    # Waypoints
    # ------------------------------------------------------------------

    def _select_type(self, t: str):
        self._selected_type.set(t)
        for name, btn in self._type_buttons.items():
            if name == t:
                btn.configure(fg_color=WP_TYPE_COLORS.get(t, COLORS["accent"]),
                               text_color="#ffffff")
            else:
                btn.configure(fg_color=COLORS["bg_input"],
                               text_color=COLORS["text_label"])

    def _add_by_position(self, dx: int, dy: int):
        pos = self._get_player_pos()
        if pos is None:
            self.app.log("Cavebot: posicao nao disponivel. Bot conectado?", COLORS["warn_yellow"])
            return
        self._do_add(pos.x + dx, pos.y + dy, pos.z)

    def _add_manual(self):
        try:
            x = int(self._var_x.get())
            y = int(self._var_y.get())
            z = int(self._var_z.get())
        except ValueError:
            self.app.log("Cavebot: X, Y, Z precisam ser inteiros.", COLORS["warn_yellow"])
            return
        self._do_add(x, y, z)
        self._var_x.set("")
        self._var_y.set("")

    def _do_add(self, x: int, y: int, z: int):
        action = self._selected_type.get().lower()
        wp = Waypoint(position=Position(x=x, y=y, z=z), action=action)
        self._section.waypoints.append(wp)
        if self._active and self._section.enabled:
            script = self._get_script()
            if script:
                script.add_waypoint(wp)
        self.app.log(
            f"[{self._section.name}] Waypoint ({x},{y},{z}) [{action}] adicionado.",
            COLORS["online_green"],
        )
        self._refresh_waypoints()
        self._refresh_section_list()

    def _delete_selected_wp(self):
        if self._selected_wp_idx is None:
            return
        idx = self._selected_wp_idx
        wps = self._section.waypoints
        if 0 <= idx < len(wps):
            wps.pop(idx)
            self._selected_wp_idx = None
            if self._active:
                script = self._get_script()
                if script:
                    self._sync_waypoints_to_script(script)
            self._refresh_waypoints()
            self._refresh_section_list()

    def _clear_waypoints(self):
        self._section.waypoints.clear()
        self._selected_wp_idx = None
        if self._active:
            script = self._get_script()
            if script:
                self._sync_waypoints_to_script(script)
        elif (script := self._get_script()):
            script.clear_waypoints()
        self._refresh_waypoints()
        self._refresh_section_list()
        self.app.log(f"Waypoints da secao '{self._section.name}' removidos.", COLORS["warn_yellow"])

    def _refresh_waypoints(self):
        if self._wp_scroll is None:
            return
        for w in self._wp_scroll.winfo_children():
            w.destroy()
        wps = self._section.waypoints
        if not wps:
            ctk.CTkLabel(
                self._wp_scroll,
                text="Nenhum waypoint nesta secao.",
                font=FONTS["small"], text_color=COLORS["text_faint"],
            ).pack(pady=20)
            return
        for idx, wp in enumerate(wps):
            is_sel = (idx == self._selected_wp_idx)
            row_bg = COLORS["accent"] + "33" if is_sel else "transparent"
            row = ctk.CTkFrame(self._wp_scroll, fg_color=row_bg, corner_radius=6)
            row.pack(fill="x", pady=2)

            action = wp.action.capitalize()
            dot_color = WP_TYPE_COLORS.get(action, COLORS["text_faint"])

            ctk.CTkLabel(
                row, text="\u25cf", font=("Segoe UI", 9),
                text_color=dot_color, width=16,
            ).pack(side="left", padx=(6, 0), pady=6)

            ctk.CTkLabel(
                row,
                text=f"{idx + 1:03d}  {action:<8}  {wp.position.x}, {wp.position.y}, {wp.position.z}",
                font=FONTS["body"], text_color=COLORS["text_label"], anchor="w",
            ).pack(side="left", fill="x", expand=True, padx=6, pady=6)

            row.bind("<Button-1>", lambda e, i=idx: self._select_wp(i))
            for child in row.winfo_children():
                child.bind("<Button-1>", lambda e, i=idx: self._select_wp(i))

    def _select_wp(self, idx: int):
        self._selected_wp_idx = idx
        self._refresh_waypoints()

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def _save_profile(self):
        filepath = filedialog.asksaveasfilename(
            initialdir=DEFAULT_WP_DIR, title="Salvar perfil",
            defaultextension=".json",
            filetypes=[("Perfil JSON", "*.json"), ("Todos", "*.*")],
        )
        if not filepath:
            return
        data = {"sections": [s.to_dict() for s in self._sections]}
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            name = os.path.splitext(os.path.basename(filepath))[0]
            self._var_profile.set(name)
            total = sum(len(s.waypoints) for s in self._sections)
            self.app.log(f"Perfil '{name}' salvo ({len(self._sections)} secoes, {total} waypoints).",
                         COLORS["online_green"])
        except Exception as e:
            self.app.log(f"Erro ao salvar: {e}", COLORS["hp_red"])

    def _load_profile(self):
        filepath = filedialog.askopenfilename(
            initialdir=DEFAULT_WP_DIR, title="Carregar perfil",
            filetypes=[("Perfil JSON", "*.json"), ("Todos", "*.*")],
        )
        if not filepath:
            return
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.app.log(f"Erro ao abrir arquivo: {e}", COLORS["hp_red"])
            return

        if isinstance(data, list):
            sec = _Section("Importado")
            for item in data:
                try:
                    sec.waypoints.append(Waypoint(
                        position=Position(x=int(item["x"]), y=int(item["y"]), z=int(item["z"])),
                        action=str(item.get("action", "walk")),
                    ))
                except (KeyError, ValueError, TypeError):
                    pass
            self._sections = [sec]
        elif isinstance(data, dict) and "sections" in data:
            self._sections = [_Section.from_dict(s) for s in data["sections"]]
            if not self._sections:
                self._sections = [_Section("Secao 1")]
        else:
            self.app.log("Formato de arquivo invalido.", COLORS["hp_red"])
            return

        self._current_section_idx = 0
        self._selected_wp_idx = None
        name = os.path.splitext(os.path.basename(filepath))[0]
        self._var_profile.set(name)
        self._refresh_section_list()
        self._refresh_waypoints()
        total = sum(len(s.waypoints) for s in self._sections)
        self.app.log(f"Perfil '{name}' carregado ({len(self._sections)} secoes, {total} waypoints).",
                     COLORS["online_green"])

    def _apply_bool(self, cfg_key, var):
        script = self._get_script()
        if script:
            script.config[cfg_key] = var.get()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build(self):
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(1, weight=1)

        self._build_topbar()
        self._build_sections()
        self._build_wp_panel()
        self._build_right_panel()

    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                           corner_radius=0, height=52)
        bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)

        self._btn_activate = ctk.CTkButton(
            bar,
            text="\u25b6  Ativar Cavebot",
            font=(FONTS["body"][0], 13, "bold") if isinstance(FONTS["body"], tuple) else FONTS["body"],
            height=36, corner_radius=10,
            fg_color=COLORS["online_green"],
            hover_color="#2e7d32",
            text_color="#ffffff",
            command=self._toggle_active,
        )
        self._btn_activate.grid(row=0, column=0, padx=(16, 8), pady=8)

        ctk.CTkLabel(
            bar, textvariable=self._var_profile,
            font=FONTS["small"], text_color=COLORS["text_faint"],
            anchor="w",
        ).grid(row=0, column=1, padx=8, sticky="w")

        pos_frame = ctk.CTkFrame(bar, fg_color=COLORS["bg_panel"], corner_radius=8)
        pos_frame.grid(row=0, column=2, padx=4, pady=8)
        ctk.CTkLabel(
            pos_frame, text="\U0001f4cd",
            font=FONTS["small"], text_color=COLORS["text_faint"],
        ).pack(side="left", padx=(8, 2))
        ctk.CTkLabel(
            pos_frame, textvariable=self._var_pos_label,
            font=FONTS["small"], text_color=COLORS["text_muted"],
        ).pack(side="left", padx=(0, 10))

        io_frame = ctk.CTkFrame(bar, fg_color="transparent")
        io_frame.grid(row=0, column=3, padx=(0, 16), pady=8)
        ctk.CTkButton(
            io_frame, text="\U0001f4be Salvar", font=FONTS["small"], height=32,
            corner_radius=8, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._save_profile,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            io_frame, text="\U0001f4c2 Carregar", font=FONTS["small"], height=32,
            corner_radius=8, fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_label"], border_width=1, border_color=COLORS["border"],
            command=self._load_profile,
        ).pack(side="left", padx=3)

    def _build_sections(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                            corner_radius=0, width=180)
        card.grid(row=1, column=0, sticky="nsew", padx=(0, 1))
        card.grid_propagate(False)
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        hdr = ctk.CTkFrame(card, fg_color=COLORS["bg_panel"], corner_radius=0, height=36)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            hdr, text="SECOES", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).grid(row=0, column=0, padx=10, sticky="w")
        hdr_btns = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_btns.grid(row=0, column=1, padx=4)
        ctk.CTkButton(
            hdr_btns, text="+", width=26, height=26, corner_radius=6,
            font=FONTS["small"],
            fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._add_section,
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            hdr_btns, text="\u2212", width=26, height=26, corner_radius=6,
            font=FONTS["small"],
            fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["hp_red"],
            command=self._remove_section,
        ).pack(side="left", padx=2)

        self._section_list_frame = ctk.CTkScrollableFrame(
            card, fg_color="transparent", corner_radius=0,
        )
        self._section_list_frame.grid(row=1, column=0, sticky="nsew")
        self._refresh_section_list()

        ctk.CTkButton(
            card, text="\u270e Renomear", font=FONTS["small"], height=28,
            corner_radius=0,
            fg_color=COLORS["bg_panel"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_faint"],
            command=self._rename_section,
        ).grid(row=2, column=0, sticky="ew")

    def _build_wp_panel(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=0)
        card.grid(row=1, column=1, sticky="nsew")
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)

        toolbar = ctk.CTkFrame(card, fg_color=COLORS["bg_card"],
                               corner_radius=0, height=40)
        toolbar.grid(row=0, column=0, sticky="ew")
        toolbar.grid_propagate(False)
        toolbar.grid_columnconfigure(0, weight=1)

        tb_btns = ctk.CTkFrame(toolbar, fg_color="transparent")
        tb_btns.grid(row=0, column=0, padx=8, pady=4, sticky="w")
        ctk.CTkButton(
            tb_btns, text="\U0001f5d1 Limpar", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["bg_input"], hover_color="#c04040",
            text_color=COLORS["hp_red"], border_width=1, border_color=COLORS["hp_red"],
            command=self._clear_waypoints,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            tb_btns, text="\u2715 Remover", font=FONTS["small"], height=28,
            corner_radius=8, fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_label"], border_width=1, border_color=COLORS["border"],
            command=self._delete_selected_wp,
        ).pack(side="left", padx=3)
        ctk.CTkButton(
            tb_btns, text="\u21ba", font=FONTS["small"], height=28, width=36,
            corner_radius=8, fg_color=COLORS["bg_input"], hover_color=COLORS["bg_hover"],
            text_color=COLORS["text_label"],
            command=self._refresh_waypoints,
        ).pack(side="left", padx=3)

        self._wp_scroll = ctk.CTkScrollableFrame(
            card, fg_color="transparent", corner_radius=0,
        )
        self._wp_scroll.grid(row=1, column=0, sticky="nsew", padx=8, pady=(4, 8))
        self._refresh_waypoints()

    def _build_right_panel(self):
        panel = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                             corner_radius=0, width=220)
        panel.grid(row=1, column=2, sticky="nsew", padx=(1, 0))
        panel.grid_propagate(False)
        panel.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(panel, fg_color="transparent", corner_radius=0)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)

        row_i = 0

        ctk.CTkLabel(
            scroll, text="TIPO", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).grid(row=row_i, column=0, padx=12, pady=(14, 6), sticky="w")
        row_i += 1

        type_grid = ctk.CTkFrame(scroll, fg_color="transparent")
        type_grid.grid(row=row_i, column=0, padx=8, pady=(0, 8), sticky="ew")
        row_i += 1
        cols = 3
        for ti, t in enumerate(WP_TYPES):
            btn = ctk.CTkButton(
                type_grid, text=t,
                width=58, height=30, corner_radius=8,
                font=FONTS["small"],
                fg_color=WP_TYPE_COLORS[t] if t == self._selected_type.get() else COLORS["bg_input"],
                hover_color=WP_TYPE_COLORS.get(t, COLORS["accent_hover"]),
                text_color="#ffffff" if t == self._selected_type.get() else COLORS["text_label"],
                border_width=0,
                command=lambda t=t: self._select_type(t),
            )
            btn.grid(row=ti // cols, column=ti % cols, padx=3, pady=3)
            self._type_buttons[t] = btn

        ctk.CTkLabel(
            scroll, text="POSICAO ATUAL", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).grid(row=row_i, column=0, padx=12, pady=(10, 4), sticky="w")
        row_i += 1

        dir_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        dir_frame.grid(row=row_i, column=0, padx=8, pady=(0, 8))
        row_i += 1
        for di, (lbl, dx, dy) in enumerate(DIRECTIONS):
            is_center = lbl == "Aqui"
            ctk.CTkButton(
                dir_frame, text=lbl,
                width=52, height=32, corner_radius=8,
                font=FONTS["small"],
                fg_color=COLORS["accent"] if is_center else COLORS["bg_input"],
                hover_color=COLORS["accent_hover"] if is_center else COLORS["bg_hover"],
                text_color="#ffffff" if is_center else COLORS["text_label"],
                border_width=0 if is_center else 1,
                border_color=COLORS["border"],
                command=lambda dx=dx, dy=dy: self._add_by_position(dx, dy),
            ).grid(row=di // 3, column=di % 3, padx=2, pady=2)

        ctk.CTkLabel(
            scroll, text="MANUAL", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).grid(row=row_i, column=0, padx=12, pady=(10, 4), sticky="w")
        row_i += 1

        manual_frame = ctk.CTkFrame(scroll, fg_color=COLORS["bg_panel"], corner_radius=10)
        manual_frame.grid(row=row_i, column=0, padx=8, pady=(0, 8), sticky="ew")
        row_i += 1
        for lbl, var, w in [("X", self._var_x, 58), ("Y", self._var_y, 58), ("Z", self._var_z, 42)]:
            r = ctk.CTkFrame(manual_frame, fg_color="transparent")
            r.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(r, text=lbl, font=FONTS["badge"],
                         text_color=COLORS["text_faint"], width=20).pack(side="left")
            ctk.CTkEntry(
                r, textvariable=var, height=28, width=w, corner_radius=6,
                fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                text_color=COLORS["text_label"], font=FONTS["body"],
            ).pack(side="left", padx=(4, 0))
        ctk.CTkButton(
            manual_frame, text="+ Adicionar", font=FONTS["small"], height=30,
            corner_radius=8, fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
            command=self._add_manual,
        ).pack(fill="x", padx=8, pady=(4, 8))

        ctk.CTkLabel(
            scroll, text="OPCOES", font=FONTS["badge"],
            text_color=COLORS["accent_light"],
        ).grid(row=row_i, column=0, padx=12, pady=(10, 4), sticky="w")
        row_i += 1

        opts = [
            ("Lootar criaturas",   "loot",              True),
            ("Atacar automatico",  "auto_attack",       True),
            ("Anti-stuck",         "enable_anti_stuck", True),
            ("Pausar em combate",  "pause_in_combat",   False),
            ("Desviar perigosos",  "avoid_dangerous",   False),
        ]
        for lbl, cfg_key, default in opts:
            var = ctk.BooleanVar(value=default)
            self._opt_vars[cfg_key] = var
            ctk.CTkSwitch(
                scroll, text=lbl, variable=var,
                font=FONTS["small"], text_color=COLORS["text_label"],
                progress_color=COLORS["accent"],
                command=lambda k=cfg_key, v=var: self._apply_bool(k, v),
            ).grid(row=row_i, column=0, padx=14, pady=4, sticky="w")
            row_i += 1
