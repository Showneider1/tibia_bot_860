"""
Painel de log na parte inferior da janela.
"""
import customtkinter as ctk
from src.ui.theme import COLORS, FONTS
from datetime import datetime


class LogPanel(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=COLORS["bg_panel"], corner_radius=0, height=130)
        self.grid_propagate(False)
        self._build()

    def _build(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=28)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        ctk.CTkLabel(header, text="  LOG", font=FONTS["badge"],
                     text_color=COLORS["text_faint"]).pack(side="left", pady=4)

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

    def log(self, msg: str, color: str = None):
        ts = datetime.now().strftime("%H:%M:%S")
        self._text.configure(state="normal")
        self._text.insert("end", f"[{ts}] {msg}\n")
        self._text.configure(state="disabled")
        self._text.see("end")
