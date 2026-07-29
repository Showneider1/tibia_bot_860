from abc import ABC, abstractmethod

class ICommandInjector(ABC):
    """Contrato para injeção de comandos (teclado/mouse/packets)."""

    @abstractmethod
    def cast_spell(self, spell_words: str) -> None:
        ...

    @abstractmethod
    def say(self, text: str) -> None:
        ...

    @abstractmethod
    def send_hotkey(self, key: str) -> bool:
        ...

    @abstractmethod
    def send_key_background(self, vk_code: int) -> bool:
        """Envia uma tecla virtual diretamente para o processo em background."""
        ...

    @abstractmethod
    def send_mouse_click(self, client_x: int, client_y: int) -> bool:
        ...

    @abstractmethod
    def tile_to_screen(
        self, tile_x: int, tile_y: int,
        player_x: int, player_y: int,
        client_width: int = 480, client_height: int = 360
    ) -> tuple:
        ...

    @abstractmethod
    def focus_client(self) -> bool:
        ...