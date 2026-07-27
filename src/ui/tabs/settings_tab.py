"""
Aba de Configuracoes gerais.

F1.4 — Todos os switches/botoes agora tem handlers reais:
  - BooleanVars persistem via engine.config (quando disponivel)
  - "Testar Conexao" chama engine._check_and_reconnect()
  - Tema (Dark/Light/Sistema) chama ctk.set_appearance_mode()
  - "Salvar Configuracoes" persiste no ProfileManager
  - Processo alvo: placeholder vem de PROCESS_NAME em addresses_860
    (com fallback seguro caso o import falhe)

F1.5 — Fix: placeholder "Not Open.exe" substituido por PROCESS_NAME real.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS

# Import seguro do PROCESS_NAME — fallback garante que a aba nao quebra
# em ambiente de desenvolvimento sem o modulo de enderecos.
try:
    from src.core.constants.addresses_860 import PROCESS_NAME as _PROCESS_NAME
except (ImportError, AttributeError):
    _PROCESS_NAME = "Tibia.exe"

# Mapeamento: chave interna -> chave em engine.config
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

        # Variaveis de preferencia
        self._pref_vars: dict = {}
        self._theme_var = ctk.StringVar(value="Dark")

        self._build()

    # ------------------------------------------------------------------
    # Helpers de acesso ao engine
    # ------------------------------------------------------------------

    def _engine(self):
        return getattr(self.app, "bot_engine", None)

    def _log(self, msg: str, color: str = None) -> None:
        """Delega ao LogPanel do app (metodo app.log)."""
        log_fn = getattr(self.app, "log", None)
        if log_fn:
            log_fn(msg, color)

    # ------------------------------------------------------------------
    # Handlers reais (F1.4)
    # ------------------------------------------------------------------

    def _on_pref_change(self, key: str, var: ctk.BooleanVar) -> None:
        """Persiste preferencia no engine.config."""
        engine = self._engine()
        if engine is None:
            return
        cfg_key = _PREF_CONFIG_KEYS.get(key)
        if cfg_key:
            engine.config[cfg_key] = var.get()

    def _on_theme_change(self, value: str) -> None:
        """Aplica tema via customtkinter e persiste em engine.config."""
        mode = _THEME_MAP.get(value, "system")
        ctk.set_appearance_mode(mode)
        self._theme_var.set(value)
        engine = self._engine()
        if engine:
            engine.config["bot.theme"] = mode

    def _on_test_connection(self) -> None:
        """Testa conexao com o processo do Tibia."""
        engine = self._engine()
        if engine is None:
            self._log("Sem BotEngine. Inicie o bot primeiro.",
                      COLORS.get("warn_yellow"))
            return
        ok = engine._check_and_reconnect()
        if ok:
            self._log("Conexao com Tibia: OK.", COLORS.get("online_green"))
        else:
            self._log("Falha na conexao. O Tibia esta aberto?",
                      COLORS.get("warn_yellow"))

    def _on_save(self) -> None:
        """Salva configuracoes via ProfileManager (se disponivel)."""
        engine = self._engine()
        if engine is None:
            self._log(
                "Configuracoes aplicadas (sem engine ativo).",
                COLORS.get("text_muted"),
            )
            return

        pm = getattr(engine, "_profile_manager", None)
        player = getattr(engine, "player", None)

        if pm and player:
            pm.save(player.name, engine.script_engine)
            self._log(f"Perfil de '{player.name}' salvo.",
                      COLORS.get("online_green"))
        else:
            self._log(
                "Configuracoes aplicadas. "
                "(ProfileManager ou player nao disponivel para persistir.)",
                COLORS.get("text_muted"),
            )

    # ------------------------------------------------------------------
    # Construcao da UI
    # ------------------------------------------------------------------

    def _build(self):
        ctk.CTkLabel(self, text="Configuracoes", font=FONTS["title"],
                     text_color=COLORS["text_primary"]).grid(
            row=0, column=0, columnspan=2, padx=24, pady=(20, 4), sticky="w")
        ctk.CTkLabel(self, text="Opcoes gerais do bot e conexao com o jogo",
                     font=FONTS["small"], text_color=COLORS["text_faint"]).grid(
            row=1, column=0, columnspan=2, padx=24, pady=(0, 16), sticky="w")

        self._conn_card()
        self._pref_card()

    def _conn_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=0, padx=(24, 8), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="CONEXAO", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, columnspan=2, padx=16, pady=(14, 10), sticky="w")

        # F1.5 fix: placeholder de processo vem de PROCESS_NAME, nao hardcoded
        conn_fields = [
            ("Processo alvo",            _PROCESS_NAME),
            ("Intervalo de tick (ms)",    "100"),
            ("Timeout de reconexao (s)",  "30"),
        ]
        for i, (lbl, placeholder) in enumerate(conn_fields):
            ctk.CTkLabel(card, text=lbl, font=FONTS["small"],
                         text_color=COLORS["text_faint"]).grid(
                row=i + 1, column=0, padx=(16, 8), pady=6, sticky="w")
            ctk.CTkEntry(
                card,
                placeholder_text=placeholder,
                height=32,
                corner_radius=8,
                fg_color=COLORS["bg_input"],
                border_color=COLORS["border"],
                text_color=COLORS["text_label"],
                font=FONTS["body"],
            ).grid(row=i + 1, column=1, padx=(0, 16), pady=6, sticky="ew")

        ctk.CTkButton(
            card,
            text="  Testar Conexao",
            font=FONTS["body"],
            height=36,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_test_connection,   # F1.4 — handler real
        ).grid(row=10, column=0, columnspan=2, padx=16, pady=(12, 16), sticky="ew")

    def _pref_card(self):
        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=14,
                            border_width=1, border_color=COLORS["border"])
        card.grid(row=2, column=1, padx=(0, 24), pady=(0, 24), sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(card, text="PREFERENCIAS", font=FONTS["badge"],
                     text_color=COLORS["accent_light"]).grid(
            row=0, column=0, padx=16, pady=(14, 10), sticky="w")

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
            ctk.CTkSwitch(
                card,
                text=lbl,
                variable=var,
                font=FONTS["body"],
                text_color=COLORS["text_label"],
                progress_color=COLORS["accent"],
                command=lambda k=key, v=var: self._on_pref_change(k, v),  # F1.4
            ).grid(row=i + 1, column=0, padx=16, pady=7, sticky="w")

        ctk.CTkLabel(card, text="Tema", font=FONTS["small"],
                     text_color=COLORS["text_faint"]).grid(
            row=10, column=0, padx=16, pady=(16, 4), sticky="w")

        ctk.CTkSegmentedButton(
            card,
            values=["Dark", "Light", "Sistema"],
            variable=self._theme_var,
            font=FONTS["body"],
            fg_color=COLORS["bg_input"],
            selected_color=COLORS["accent"],
            selected_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text_label"],
            command=self._on_theme_change,      # F1.4 — handler real
        ).grid(row=11, column=0, padx=16, pady=(0, 12), sticky="ew")

        ctk.CTkButton(
            card,
            text="  Salvar Configuracoes",
            font=FONTS["body"],
            height=36,
            corner_radius=10,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_save,              # F1.4 — handler real
        ).grid(row=12, column=0, padx=16, pady=(4, 16), sticky="ew")
