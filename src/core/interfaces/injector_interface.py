from abc import ABC, abstractmethod

class ICommandInjector(ABC):
    """Contrato para injeção de comandos (teclado/mouse/packets)."""

    @abstractmethod
    def cast_spell(self, spell_words: str) -> None:
        ...

    @abstractmethod
    def send_hotkey(self, key: str) -> None:
        ...

    @abstractmethod
    def send_key_background(self, vk_code: int) -> None:
        """Envia uma tecla virtual diretamente para o processo em background."""
        ...

    @abstractmethod
    def focus_client(self) -> bool:
        ...