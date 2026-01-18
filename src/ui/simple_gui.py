import threading
import tkinter as tk
from tkinter import ttk
from src.main import TibiaBot  # vamos ajustar o main para expor a classe


class BotGUI:
    def __init__(self, root: tk.Tk, config_path: str = "config.yaml"):
        self.root = root
        self.root.title("TibiaBot 8.60")
        self.root.geometry("400x220")
        self.root.resizable(False, False)

        # Estado
        self.bot = TibiaBot(config_path=config_path)
        self.bot_thread = None

        # UI
        self._build_ui()

    def _build_ui(self):
        padding = {"padx": 10, "pady": 5}

        self.lbl_status = ttk.Label(self.root, text="Status: Desconectado", foreground="red")
        self.lbl_status.pack(**padding)

        self.lbl_bot = ttk.Label(self.root, text="Bot: DESLIGADO", foreground="red")
        self.lbl_bot.pack(**padding)

        frm_buttons = ttk.Frame(self.root)
        frm_buttons.pack(pady=10)

        self.btn_start = ttk.Button(frm_buttons, text="Iniciar Bot", command=self.start_bot)
        self.btn_start.grid(row=0, column=0, padx=5)

        self.btn_toggle = ttk.Button(frm_buttons, text="Ligar Bot", command=self.toggle_bot, state="disabled")
        self.btn_toggle.grid(row=0, column=1, padx=5)

        self.btn_stop = ttk.Button(frm_buttons, text="Encerrar", command=self.on_close, state="disabled")
        self.btn_stop.grid(row=0, column=2, padx=5)

        self.txt_log = tk.Text(self.root, height=6, state="disabled")
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=5)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def log(self, msg: str):
        self.txt_log.configure(state="normal")
        self.txt_log.insert("end", msg + "\n")
        self.txt_log.see("end")
        self.txt_log.configure(state="disabled")

    def start_bot(self):
        self.log("Inicializando bot...")
        ok = self.bot.initialize()
        if not ok:
            self.log("Falha ao inicializar bot. Veja logs.")
            return

        self.lbl_status.config(text="Status: Conectado", foreground="green")
        self.btn_start.config(state="disabled")
        self.btn_toggle.config(state="normal")
        self.btn_stop.config(state="normal")

        # roda loop do bot em thread separada
        self.bot_thread = threading.Thread(target=self.bot.run, daemon=True)
        self.bot_thread.start()
        self.log("Bot iniciado. Use 'Ligar Bot' para ativar lógica.")

    def toggle_bot(self):
        if not self.bot or not self.bot.bot_engine:
            return
        self.bot._toggle_bot()
        if self.bot.bot_engine.enabled:
            self.lbl_bot.config(text="Bot: LIGADO", foreground="green")
            self.log("Bot LIGADO.")
            self.btn_toggle.config(text="Desligar Bot")
        else:
            self.lbl_bot.config(text="Bot: DESLIGADO", foreground="red")
            self.log("Bot DESLIGADO.")
            self.btn_toggle.config(text="Ligar Bot")

    def on_close(self):
        self.log("Encerrando...")
        if self.bot:
            self.bot._running = False
        self.root.after(300, self.root.destroy)


def main_gui():
    root = tk.Tk()
    gui = BotGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main_gui()
