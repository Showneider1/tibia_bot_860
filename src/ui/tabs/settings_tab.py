import customtkinter as ctk
from src.ui.theme import COLORS, FONTS

try:
    from src.core.constants.addresses_860 import PROCESS_NAME as _PROCESS_NAME
except (ImportError, AttributeError):
    _PROCESS_NAME = "Tibia.exe"

_PREF_CONFIG_KEYS = {
    "start_on_open":  "bot.start_on_open",
    "minimize_tray":  "bot.minimize_tray",
    "sound_levelup":  "bot.sound_levelup",
    "debug_logs":     "bot.debug_logs",
    "auto_reconnect": "bot.auto_reconnect",
}

_THEME_MAP = {
    "Dark":    "dark",
    "Light":   "light",
    "Sistema": "system",
}


class SettingsTab(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg_dark"], corner_radius=0)
        self.app = app
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._pref_vars: dict = {}
        self._theme_var = ctk.StringVar(value="Dark")
        self._build()

    def _engine(self):
        return getattr(self.app, "bot_engine", None)

    def _log(self, msg: str, color: str = None) -> None:
        log_fn = getattr(self.app, "log", None)
        if log_fn:
            log_fn(msg, color)

    def _on_pref_change(self, key: str, var: ctk.BooleanVar) -> None:
        engine = self._engine()
        if engine is None:
            return
        cfg_key = _PREF_CONFIG_KEYS.get(key)
        if cfg_key:
            engine.config[cfg_key] = var.get()

    def _on_theme_change(self, value: str) -> None:
        mode = _THEME_MAP.get(value, "system")
        ctk.set_appearance_mode(mode)
        self._theme_var.set(value)
        engine = self._engine()
        if engine:
            engine.config["bot.theme"] = mode

    def _on_test_connection(self) -> None:
        engine = self._engine()
        if engine is None:
            self._log("Sem BotEngine.", COLORS["warn_yellow"])
            return
        ok = engine.check_and_reconnect()
        if ok:
            self._log("Conexao: OK.", COLORS["online_green"])
        else:
            self._log("Falha na conexao.", COLORS["warn_yellow"])

    def _on_save(self) -> None:
        engine = self._engine()
        if engine is None:
            self._log("Config aplicadas (sem engine).", COLORS["text_muted"])
            return
        pm = getattr(engine, "_profile_manager", None)
        player = getattr(engine, "player", None)
        if pm and player:
            pm.save(player.name, engine.script_engine)
            self._log(f"Perfil salvo.", COLORS["online_green"])
        else:
            self._log("Config aplicadas.", COLORS["text_muted"])

    def _build(self):
        ctk.CTkLabel(self, text="Configuracoes", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(self, text="Opcoes gerais do bot",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=16, pady=(0, 10), sticky="w")
        self._conn_card()
        self._pref_card()

    def _conn_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=0, padx=(16, 6), pady=(0, 16), sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="CONEXAO", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=12, pady=(10, 6), sticky="w")

        conn_fields = [
            ("Processo alvo",            _PROCESS_NAME),
            ("Intervalo tick (ms)",      "100"),
            ("Timeout reconexao (s)",    "30"),
        ]
        for i, (lbl, placeholder) in enumerate(conn_fields):
            ctk.CTkLabel(card, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=i+1, column=0, padx=(12, 6), pady=4, sticky="w")
            ctk.CTkEntry(card, placeholder_text=placeholder, height=28, corner_radius=6,
                         fg_color=COLORS["bg_input"], border_color=COLORS["border"],
                         text_color=COLORS["text_label"], font=FONTS["body"]).grid(
                row=i+1, column=1, padx=(0, 12), pady=4, sticky="ew")

        ctk.CTkButton(card, text="  Testar Conexao", font=FONTS["body"],
                      height=32, corner_radius=8,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._on_test_connection).grid(
            row=10, column=0, columnspan=2, padx=12, pady=(8, 12), sticky="ew")

    def _pref_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=12,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=1, padx=(6, 16), pady=(0, 16), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="PREFERENCIAS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=12, pady=(10, 6), sticky="w")

        prefs = [
            ("start_on_open", "Iniciar bot ao abrir",    False),
            ("minimize_tray", "Minimizar na bandeja",    True),
            ("sound_levelup", "Som ao level up",         True),
            ("debug_logs",    "Logs detalhados (DEBUG)", False),
            ("auto_reconnect","Auto-reconnect",          True),
        ]
        for i, (key, lbl, default) in enumerate(prefs):
            var = ctk.BooleanVar(value=default)
            self._pref_vars[key] = var
            ctk.CTkSwitch(card, text=lbl, variable=var, font=FONTS["small"],
                          text_color=COLORS["text_label"], progress_color=COLORS["accent"],
                          command=lambda k=key, v=var: self._on_pref_change(k, v)).grid(
                row=i+1, column=0, padx=12, pady=5, sticky="w")

        ctk.CTkLabel(card, text="Tema", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=10, column=0, padx=12, pady=(12, 2), sticky="w")
        ctk.CTkSegmentedButton(card, values=["Dark", "Light", "Sistema"],
                               variable=self._theme_var, font=FONTS["body"],
                               fg_color=COLORS["bg_input"],
                               selected_color=COLORS["accent"],
                               selected_hover_color=COLORS["accent_hover"],
                               text_color=COLORS["text_label"],
                               command=self._on_theme_change).grid(
            row=11, column=0, padx=12, pady=(0, 8), sticky="ew")

        ctk.CTkButton(card, text="  Salvar Configuracoes", font=FONTS["body"],
                      height=32, corner_radius=8,
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      command=self._on_save).grid(
            row=12, column=0, padx=12, pady=(4, 12), sticky="ew")
