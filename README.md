# TibiaBot 860

Bot para Tibia 8.60 / servidores Kaldrox com interface grafica customtkinter.

## Requisitos

- Windows (obrigatorio — usa Win32 API para leitura de memoria)
- Python 3.10+
- Tibia 8.60 ou servidor Kaldrox **aberto e logado**
- Executar como **Administrador**

## Instalacao

```bash
# 1. Clone o repositorio
git clone https://github.com/Showneider1/tibia_bot_860.git
cd tibia_bot_860

# 2. Crie e ative o venv
python -m venv venv
.\venv\Scripts\activate

# 3. Instale as dependencias
pip install -r requirements.txt
```

## Como rodar

```bash
# Interface grafica (recomendado)
python gui.py

# Bot headless (terminal)
python -m src.main
```

> **Atencao:** Execute sempre como Administrador. Sem permissao de Admin o
> `OpenProcess` falha e o bot nao consegue ler a memoria do Tibia.

## Arquitetura

```
tibia_bot_860/
├── gui.py                          # Entry point da UI
├── src/
│   ├── ui/                         # Interface grafica (customtkinter)
│   │   ├── app.py                  # Janela principal + integracao engine
│   │   ├── theme.py                # Cores e fontes
│   │   ├── tabs/                   # Abas: Status, Healing, Cavebot, Config
│   │   └── widgets/                # Sidebar, LogPanel
│   ├── application/
│   │   ├── bot_engine.py           # Loop principal + eventos + scripts
│   │   ├── events/                 # EventManager + EventType
│   │   └── scripts/                # ScriptEngine
│   ├── infrastructure/
│   │   ├── memory/
│   │   │   ├── memory_reader.py    # Leitura Win32 (suporte 32-bit)
│   │   │   └── process_manager.py  # Handle do processo
│   │   ├── readers/
│   │   │   ├── player_reader.py    # Leitura dos dados do player
│   │   │   └── creature_reader.py  # Leitura da BattleList
│   │   └── injection/
│   │       └── keyboard_injector.py
│   └── core/
│       ├── entities/               # Player, Creature
│       ├── value_objects/          # Address, Position, Stats
│       ├── constants/
│       │   └── addresses_860.py    # Enderecos de memoria do cliente 8.60
│       └── exceptions/
└── requirements.txt
```

## Fluxo de dados

```
Tibia.exe (processo)
    |
    | ReadProcessMemory (Win32 API)
    |
MemoryReader  <--  ProcessManager (handle + base_address)
    |
    +-- PlayerReader   --> Player (hp, mana, posicao, stamina...)
    +-- CreatureReader --> [Creature, ...] (BattleList)
    |
BotEngine.tick()
    |
    +-- _update_state()   -> atualiza self.player + self.creatures
    +-- _process_events() -> emite eventos (HP baixo, level up...)
    +-- _run_scripts()    -> executa scripts registrados
    |
BotApp.update_from_engine(player)
    |
    +-- StatusTab.refresh() -> atualiza UI (thread-safe via root.after)
```

## Integracao UI + BotEngine

Por padrao a UI abre em modo demo (dados zerados, sem leitura de memoria).
Para conectar ao jogo:

```python
from src.application.bot_engine import BotEngine
from src.infrastructure.memory.process_manager import ProcessManager
from src.infrastructure.memory.memory_reader import MemoryReader
from src.infrastructure.injection.keyboard_injector import KeyboardInjector
from src.core.constants.addresses_860 import PLAYER, BATTLE_LIST, CREATURE
from src.ui.app import BotApp

pm = ProcessManager()
mr = MemoryReader(pm)
ki = KeyboardInjector()

engine = BotEngine(pm, mr, ki, PLAYER, BATTLE_LIST, CREATURE)

app = BotApp()
app.bot_engine = engine  # injeta antes de run()
app.run()
```

Ao clicar em **INICIAR BOT** a UI chama `engine.start()`, anexa ao processo
e inicia o loop de leitura em thread separada.

## Changelog

### v1.1.0 (2026-07-27)
- **fix:** `_update_state` estava fora da classe `BotEngine` (bug de indentacao)
  causando `AttributeError` silencioso em `tick()`
- **fix:** `_connection_retry_count` e `_max_retry_attempts` nao inicializados
- **fix:** import duplicado de `EventManager`/`EventType` removido
- **fix:** `_player_data` (renomeado de `_mock_player`) propagado em todos os arquivos
- **fix:** HP/Mana com clamp — nunca exibe valor maior que o maximo
- **fix:** simulacao aleatoria de HP removida — dados so mudam com leitura real
- **improvement:** debounce em eventos `PLAYER_HEALTH_LOW` e `PLAYER_MANA_LOW`
- **improvement:** `update_from_engine()` com fallback seguro via `getattr` + `.get()`
- **improvement:** `_start_engine_loop()` com try/except para nao silenciar erros
- **improvement:** `gui.py` documentado com instrucoes de integracao
- **docs:** README reescrito com arquitetura, fluxo de dados e exemplos

### v1.0.0 (2026-07-26)
- Interface grafica inicial (Status, Healing, Cavebot, Config)
- Leitura de memoria via Win32 API com suporte a processos 32-bit
- MemoryReader com cache TTL
- ProcessManager com fallback PROCESS_ALL_ACCESS
- BotEngine com ScriptEngine e EventManager
