"""
BotEngine - nucleo do bot Tibia 8.60.
Gerencia loop principal, leitura de memoria, scripts e eventos.
"""
import time
from typing import Optional, Dict, Any, List

import win32gui
try:
    import win32process
except ImportError:
    win32process = None

from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.memory.memory_writer import MemoryWriter
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.infrastructure.injection.memory_walker import MemoryWalker
from src.infrastructure.logging.logger import get_logger

from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.address import MemoryAddress

from src.application.events.event_manager import EventManager
from src.application.events.event_types import EventType
from src.application.scripts.script_engine import ScriptEngine

from src.infrastructure.readers.player_reader import PlayerReader
from src.infrastructure.readers.creature_reader import CreatureReader

__all__ = ["BotEngine", "EventType", "EventManager"]


class BotEngine:
    """
    Engine principal do bot.

    Responsabilidades:
      - Conectar ao processo Tibia via ProcessManager
      - Ler dados do player e criaturas a cada tick
      - Disparar eventos (HP baixo, level up, criatura detectada...)
      - Executar scripts registrados no ScriptEngine
    """

    _HEALTH_EVENT_DEBOUNCE = 10
    _MAX_RETRY_ATTEMPTS = 5

    def __init__(
        self,
        process_manager: ProcessManager,
        memory_reader: MemoryReader,
        keyboard_injector: KeyboardInjector,
        player_addresses: Dict[str, Any],
        battle_list_addresses: Dict[str, Any],
        creature_offsets: Dict[str, int],
        memory_writer: Optional[MemoryWriter] = None,
    ):
        self._log = get_logger("BotEngine")

        self._pm = process_manager
        self._memory = memory_reader
        self._injector = keyboard_injector

        # MemoryWriter: se nao fornecido, cria usando o mesmo process_manager.
        if memory_writer is None:
            memory_writer = MemoryWriter(process_manager)
        self._memory_writer = memory_writer

        # MemoryWalker v4: usa PostMessage via KeyboardInjector.
        # O injector e injetado em start() apos o PID ser configurado.
        self._walker = MemoryWalker()

        self._player_reader = PlayerReader(self._memory, player_addresses)
        self._creature_reader = CreatureReader(
            self._memory, battle_list_addresses, creature_offsets
        )

        self.enabled: bool = False
        self.config: Dict[str, Any] = {
            "player_vocation": "Auto",
            "use_script_engine": True,
            "combat_mode": "lowest_hp",
        }

        self.player: Optional[Player] = None
        self.creatures: List[Creature] = []

        self.script_engine = ScriptEngine()
        self.event_manager = EventManager()

        self._last_player: Optional[Player] = None
        self._last_creatures: List[Creature] = []

        self._connected: bool = False
        self._connection_retry_count: int = 0
        self._health_low_ticks: int = 0
        self._mana_low_ticks: int = 0

        # F1.3 - ProfileManager injetado via set_profile_manager() para evitar
        # import circular (BotEngine nao importa ProfileManager diretamente).
        self._profile_manager = None

    # ------------------------------------------------------------------
    # Properties publicas
    # ------------------------------------------------------------------

    @property
    def injector(self) -> KeyboardInjector:
        """KeyboardInjector para hotkeys, spells e healing."""
        return self._injector

    @property
    def walker(self) -> MemoryWalker:
        """
        MemoryWalker v4: movimento via PostMessage WM_KEYDOWN/WM_KEYUP.
        Delega para KeyboardInjector.send_key_background(vk).
        Interface publica: walk_to / cooldown_passed / reset.
        """
        return self._walker

    @property
    def memory_writer(self) -> MemoryWriter:
        """MemoryWriter direto, para uso avancado pelos scripts."""
        return self._memory_writer

    # ------------------------------------------------------------------
    # Resolucao de HWND (mantida para cast_spell / focus_client)
    # ------------------------------------------------------------------

    def _resolve_hwnd(self, pid: int) -> Optional[int]:
        """
        Encontra o HWND da janela principal do Tibia dado o PID do processo.
        Usa win32process.GetWindowThreadProcessId para filtrar por PID exato.
        Fallback: busca por titulo contendo 'Tibia'.
        """
        if win32process is None:
            return None

        result: list[int] = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                try:
                    _, hwnd_pid = win32process.GetWindowThreadProcessId(hwnd)
                except Exception:
                    return True
                if hwnd_pid == pid:
                    result.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(callback, None)
        except Exception as e:
            self._log.debug(f"EnumWindows(pid) falhou: {e}")

        if result:
            hwnd = result[0]
            self._log.debug(f"HWND resolvido via PID={pid}: {hwnd:#010x}")
            return hwnd

        result2: list[int] = []

        def callback2(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and "tibia" in title.lower():
                    result2.append(hwnd)
            return True

        try:
            win32gui.EnumWindows(callback2, None)
        except Exception:
            pass

        if result2:
            self._log.debug(f"HWND resolvido via titulo: {result2[0]:#010x}")
            return result2[0]

        return None

    # ------------------------------------------------------------------
    # Integracao com ProfileManager (F1.3)
    # ------------------------------------------------------------------

    def set_profile_manager(self, profile_manager) -> None:
        """
        Injeta o ProfileManager e registra o handler PLAYER_LOADED.
        Deve ser chamado apos BotApp.set_bot_engine(), antes do loop.
        """
        self._profile_manager = profile_manager
        self.event_manager.subscribe(
            EventType.PLAYER_LOADED,
            self._on_player_loaded,
        )
        self._log.info("ProfileManager registrado no BotEngine.")

    def _on_player_loaded(self, **kwargs) -> None:
        """Carrega o perfil do personagem ao detectar o primeiro tick valido."""
        player = kwargs.get("player")
        if player and self._profile_manager:
            try:
                self._profile_manager.load(player.name, self.script_engine)
                self._log.info(f"Perfil carregado para '{player.name}'.")
            except Exception as e:
                self._log.warning(f"Erro ao carregar perfil de '{player.name}': {e}")

    # ------------------------------------------------------------------
    # Ciclo de vida
    # ------------------------------------------------------------------

    def start(self) -> bool:
        """Conecta ao processo do Tibia e inicializa todos os componentes."""
        try:
            if not self._pm.is_running():
                if not self._pm.attach():
                    self._log.error("Falha ao anexar ao processo Tibia.")
                    return False

            self._connected = True
            self._connection_retry_count = 0

            pid = getattr(self._pm, "process_id", None)
            if pid is not None:
                # Propaga PID ao KeyboardInjector (PostMessage + cast_spell)
                try:
                    self._injector.set_process_id(pid)
                except Exception as e:
                    self._log.debug(f"Nao foi possivel setar PID no injector: {e}")

                # Injeta KeyboardInjector no MemoryWalker v4 (PostMessage)
                # Deve ocorrer APOS set_process_id para garantir PID configurado.
                self._walker.set_injector(self._injector)
                self._log.debug("KeyboardInjector injetado no MemoryWalker.")

                # Propaga HWND ao KeyboardInjector para focus_client / cast_spell
                hwnd = self._resolve_hwnd(pid)
                if hwnd:
                    try:
                        self._injector._hwnd = hwnd
                        self._log.debug(f"HWND={hwnd:#010x} propagado ao injector.")
                    except Exception:
                        pass
                else:
                    self._log.warning(
                        "HWND nao encontrado para PID=%d; "
                        "cast_spell fara EnumWindows no primeiro uso.", pid
                    )

            self._log.info("Bot conectado ao processo Tibia.")
            self._log.info(
                f"Script Engine pronto ({len(self.script_engine.list_scripts())} scripts)."
            )
            return True

        except Exception as e:
            self._log.error(f"Erro ao conectar ao Tibia: {e}", exc_info=True)
            self._connected = False
            return False

    def stop(self) -> None:
        """Desconecta e limpa o estado."""
        self.enabled = False
        self._connected = False
        self._walker.reset()
        self._pm.detach()
        self._log.info("BotEngine parado.")

    def tick(self) -> None:
        """
        Executa um ciclo completo:
          1. Leitura de memoria
          2. Disparo de eventos
          3. Execucao de scripts (se habilitado)
        """
        if not self._connected:
            return

        start_time = time.perf_counter()

        self._update_state()
        self._process_events()

        if self.enabled and self.config.get("use_script_engine", True):
            self._run_scripts()

        elapsed = (time.perf_counter() - start_time) * 1000
        if elapsed > 50:
            self._log.debug(f"Tick lento: {elapsed:.1f}ms")

    def run_loop(self, interval: float = 0.1) -> None:
        """Loop autonomo com controle de tempo."""
        self._log.info("BotEngine loop iniciado.")
        try:
            while True:
                start = time.perf_counter()
                self.tick()
                elapsed = time.perf_counter() - start
                time.sleep(max(0, interval - elapsed))
        except KeyboardInterrupt:
            self._log.info("Loop interrompido pelo usuario.")
        finally:
            self.stop()

    # ------------------------------------------------------------------
    # Leitura de estado
    # ------------------------------------------------------------------

    def _update_state(self) -> None:
        """
        Le a memoria e atualiza self.player e self.creatures.

        F1.2 - Apos ler o player, propaga player.vocation para
        engine.config["player_vocation"] quando a vocacao for valida.

        Sincroniza posicao e nome reais via BattleList.
        """
        self._last_player = self.player
        self._last_creatures = list(self.creatures)

        try:
            self.player = self._player_reader.get_player()
            self.creatures = self._creature_reader.get_creatures()

            if self.player and self.player.vocation not in ("Unknown", "Auto", "", None):
                if not str(self.player.vocation).startswith("Unknown("):
                    self.config["player_vocation"] = self.player.vocation

            if self.player and self.creatures:
                for creature in self.creatures:
                    if creature.id == self.player.id:
                        self.player.position = creature.position
                        if creature.name and creature.name not in ("Unknown", ""):
                            self.player.name = creature.name
                        break

        except Exception as e:
            self._log.error(f"Erro ao atualizar estado: {e}", exc_info=True)

    def _check_and_reconnect(self) -> bool:
        try:
            self._memory.read_int(MemoryAddress(0x63FE8C))
            self._connection_retry_count = 0
            return True
        except Exception:
            self._connection_retry_count += 1
            if self._connection_retry_count >= self._MAX_RETRY_ATTEMPTS:
                self._log.warning(
                    f"Conexao perdida apos {self._MAX_RETRY_ATTEMPTS} tentativas."
                )
                self._connected = False
                self.event_manager.emit(EventType.CONNECTION_LOST)
            else:
                self._log.debug(
                    f"Reconexao tentativa "
                    f"{self._connection_retry_count}/{self._MAX_RETRY_ATTEMPTS}..."
                )
            return False

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _process_events(self) -> None:
        """Compara o estado atual com o anterior e dispara eventos."""
        if not self.player:
            return

        if self._last_player is None:
            self._log.info(
                f"Player carregado: ID={self.player.id} Name='{self.player.name}' "
                f"HP={self.player.stats.health}/{self.player.stats.max_health}"
            )
            self.event_manager.emit(EventType.PLAYER_LOADED, player=self.player)

        if self.player.hp_percent() < 30:
            self._health_low_ticks += 1
            if (
                self._health_low_ticks == 1
                or self._health_low_ticks % self._HEALTH_EVENT_DEBOUNCE == 0
            ):
                self.event_manager.emit(EventType.PLAYER_HEALTH_LOW, player=self.player)
        else:
            self._health_low_ticks = 0

        if self.player.mana_percent() < 20:
            self._mana_low_ticks += 1
            if (
                self._mana_low_ticks == 1
                or self._mana_low_ticks % self._HEALTH_EVENT_DEBOUNCE == 0
            ):
                self.event_manager.emit(EventType.PLAYER_MANA_LOW, player=self.player)
        else:
            self._mana_low_ticks = 0

        if self._last_player and self.player.level > self._last_player.level:
            self._log.info(f"Level Up! {self._last_player.level} -> {self.player.level}")
            self.event_manager.emit(EventType.LEVEL_UP, player=self.player)

        last_ids = {c.id for c in self._last_creatures}
        for creature in self.creatures:
            if creature.id not in last_ids:
                self.event_manager.emit(
                    EventType.CREATURE_DETECTED,
                    creature=creature,
                    player=self.player,
                )

    # ------------------------------------------------------------------
    # Scripts
    # ------------------------------------------------------------------

    def _run_scripts(self) -> None:
        """Executa todos os scripts registrados com o contexto atual."""
        context = {
            "player": self.player,
            "creatures": self.creatures,
            "bot_engine": self,
        }
        self.script_engine.execute_all(context)
