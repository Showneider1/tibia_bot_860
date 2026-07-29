import customtkinter as ctk
from src.ui.theme import COLORS, FONTS
from datetime import datetime

_COLOR_TAGS: dict = {}


class LogPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_panel"], corner_radius=0, height=100)
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=22)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(header, text="  LOG", font=FONTS["badge"],
                     text_color=COLORS["text_faint"]).pack(side="left", pady=3)

        self._clear_btn = ctk.CTkButton(
            header, text="X", font=FONTS["small"], width=20, height=16,
            corner_radius=4, fg_color="transparent",
            text_color=COLORS["text_faint"], hover_color=COLORS["bg_hover"],
            command=self._clear,
        )
        self._clear_btn.pack(side="right", padx=(0, 6))

        self._text = ctk.CTkTextbox(
            self,
            font=FONTS["mono"],
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text_muted"],
            corner_radius=0,
            wrap="word",
            state="disabled",
        )
        self._text.grid(row=1, column=0, sticky="nsew")
        self._configure_color_tags()

    def _configure_color_tags(self) -> None:
        default_tags = {
            "default": COLORS.get("text_muted", "#9e9e9e"),
            "green":   COLORS.get("online_green", "#4caf50"),
            "yellow":  COLORS.get("warn_yellow", "#ffc107"),
            "red":     COLORS.get("hp_red", "#f44336"),
            "blue":    COLORS.get("mana_blue", "#2196f3"),
            "faint":   COLORS.get("text_faint", "#616161"),
            "accent":  COLORS.get("accent_light", "#7986cb"),
        }
        tk_widget = self._text._textbox
        for tag_name, color in default_tags.items():
            tk_widget.tag_config(tag_name, foreground=color)
            _COLOR_TAGS[color.lower()] = tag_name

    def _resolve_tag(self, color: str | None) -> str:
        if color is None:
            return "default"
        normalized = color.lower().strip()
        if normalized in _COLOR_TAGS:
            return _COLOR_TAGS[normalized]
        tag_name = f"dyn_{normalized.lstrip('#')}"
        if tag_name not in _COLOR_TAGS.values():
            try:
                self._text._textbox.tag_config(tag_name, foreground=color)
                _COLOR_TAGS[normalized] = tag_name
            except Exception:
                return "default"
        return tag_name

    def log(self, msg: str, color: str = None) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        tag = self._resolve_tag(color)
        self._text.configure(state="normal")
        self._text._textbox.insert("end", f"[{ts}] {msg}\n", tag)
        self._text.configure(state="disabled")
        self._text.see("end")

    def _clear(self) -> None:
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.configure(state="disabled")
