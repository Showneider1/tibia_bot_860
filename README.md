# TibiaBot 860

> Bot para **Tibia 8.60 / servidores Kaldrox** com interface gráfica customtkinter,
> leitura de memória via Win32 API, cavebot com A\* pathfinding e sistema de scripts.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![Version](https://img.shields.io/badge/Version-1.2.0-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## Sumário

- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Como rodar](#como-rodar)
- [Arquitetura](#arquitetura)
- [Módulos](#módulos)
- [Fluxo de dados](#fluxo-de-dados)
- [Cavebot](#cavebot)
- [Scripts disponíveis](#scripts-disponíveis)
- [Integração UI + BotEngine](#integração-ui--botengine)
- [Endereços de memória](#endereços-de-memória)
- [Changelog](#changelog)

---

## Requisitos

| Requisito | Detalhe |
|---|---|
| **OS** | Windows 10/11 (obrigatório — usa Win32 API) |
| **Python** | 3.10 ou superior |
| **Cliente** | Tibia 8.60 ou servidor Kaldrox **aberto e logado** |
| **Permissão** | Executar como **Administrador** (necessário para `OpenProcess`) |

---

## Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/Showneider1/tibia_bot_860.git
cd tibia_bot_860

# 2. Crie e ative o venv
python -m venv venv
.\venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

> **Atenção:** Execute sempre como Administrador.  
> Sem permissão de Admin o `OpenProcess` falha silenciosamente e o bot
> não consegue ler a memória do Tibia.

---

## Como rodar

```bash
# Interface gráfica (recomendado)
python gui.py

# Bot headless (terminal)
python -m src.main
```

### Fluxo básico de uso

1. Abra o Tibia 8.60 e faça login com seu personagem
2. Execute `python gui.py` **como Administrador**
3. Clique em **INICIAR BOT** — o bot conecta ao processo e começa a ler memória
4. Na aba **Cavebot**, adicione waypoints com o grid direcional ou manualmente
5. Clique em **Ativar Cavebot** — o personagem começa a andar

---

## Arquitetura

```
tibia_bot_860/
├── gui.py                              # Entry point da UI (customtkinter)
├── src/
│   ├── ui/                             # Camada de interface
│   │   ├── app.py                      # Janela principal + integração engine
│   │   ├── theme.py                    # Cores, fontes e tokens visuais
│   │   ├── tabs/
│   │   │   ├── status_tab.py           # HP, Mana, posição, stats do player
│   │   │   ├── healing_tab.py          # Configuração de cura automática
│   │   │   ├── cavebot_tab.py          # Waypoints, seções, ativar/desativar
│   │   │   └── config_tab.py           # Configurações gerais do bot
│   │   └── widgets/
│   │       ├── sidebar.py              # Navegação lateral
│   │       └── log_panel.py            # Painel de log em tempo real
│   ├── application/
│   │   ├── bot_engine.py               # Loop principal, eventos e scripts
│   │   ├── events/
│   │   │   ├── event_manager.py        # Pub/sub de eventos
│   │   │   └── event_types.py          # Enum de tipos de evento
│   │   └── scripts/
│   │       ├── base_script.py          # Classe base (on_enable/on_disable)
│   │       ├── script_engine.py        # Orquestrador de scripts
│   │       ├── cavebot_script.py       # Navegação A* + anti-stuck + follow
│   │       ├── healing_script.py       # Cura automática por HP/Mana%
│   │       └── buff_script.py          # Magias de buff periódicas
│   ├── infrastructure/
│   │   ├── memory/
│   │   │   ├── memory_reader.py        # ReadProcessMemory 32-bit com cache TTL
│   │   │   └── process_manager.py      # Handle Win32 + base_address
│   │   ├── readers/
│   │   │   ├── player_reader.py        # Leitura dos dados do player
│   │   │   └── creature_reader.py      # Leitura da BattleList (até 13 criaturas)
│   │   ├── injection/
│   │   │   └── keyboard_injector.py    # PostMessage background (lParam correto)
│   │   └── logging/
│   │       └── logger.py               # Logger centralizado
│   ├── core/
│   │   ├── entities/
│   │   │   ├── player.py               # Entidade Player (hp, mana, pos, stats)
│   │   │   ├── creature.py             # Entidade Creature (id, nome, hp, pos)
│   │   │   └── waypoint.py             # Entidade Waypoint (position + action)
│   │   ├── value_objects/
│   │   │   ├── position.py             # Position(x,y,z) + distance_chebyshev()
│   │   │   ├── address.py              # MemoryAddress tipado
│   │   │   └── stats.py                # PlayerStats (health, mana, maxes)
│   │   ├── interfaces/
│   │   │   └── injector_interface.py   # ICommandInjector (ABC)
│   │   └── constants/
│   │       └── addresses_860.py        # Endereços de memória do cliente 8.60
│   └── ai/
│       └── pathfinding/
│           ├── astar.py                # Algoritmo A* puro
│           └── pathfinder.py           # Wrapper + cache de rotas
├── data/                               # JSONs de waypoints e configurações
├── docs/                               # Documentação extra
├── examples/                           # Exemplos de uso da API
├── scripts/                            # Scripts utilitários
└── tests/                              # Testes automatizados
```

---

## Módulos

### `BotEngine` — `src/application/bot_engine.py`

Núcleo do bot. Gerencia o loop de tick, leitura de memória, eventos e execução de scripts.

```python
engine.start()        # Conecta ao processo Tibia
engine.tick()         # Um ciclo: lê memória → eventos → scripts
engine.stop()         # Desconecta
engine.injector       # Property pública → KeyboardInjector
engine.script_engine  # ScriptEngine com todos os scripts registrados
engine.player         # Player atual (atualizado a cada tick)
engine.creatures      # Lista de Creature da BattleList
```

### `KeyboardInjector` — `src/infrastructure/injection/keyboard_injector.py`

Envia teclas ao cliente Tibia em **background** via `PostMessage` (sem precisar
que a janela esteja em foco).

```python
injector.send_key_background(win32con.VK_UP)   # Anda para cima
injector.cast_spell("exura")                    # Digita magia + Enter
injector.send_hotkey("F1")                      # Envia F1-F12
```

> **Importante:** O `lParam` de cada tecla é montado com scancode correto +
> extended key flag. Setas usam `extended=True` (bit 24).  
> Sem isso o Tibia 8.60 ignora o `WM_KEYDOWN` silenciosamente.

### `CavebotScript` — `src/application/scripts/cavebot_script.py`

Script de navegação automática com A\* pathfinding, anti-stuck e modo follow.

```python
script.add_waypoint(wp)   # Adiciona waypoint à rota
script.clear_waypoints()  # Limpa todos os waypoints
script.start_follow("PlayerName", distance=2)  # Modo follow
script.stop_follow()      # Para o follow
script.get_status()       # Dict com status atual
```

---

## Fluxo de dados

```
Tibia.exe (processo 32-bit)
        │
        │  ReadProcessMemory (Win32 API)
        │
  ProcessManager ──► base_address, handle
        │
  MemoryReader (cache TTL 50ms)
        │
        ├── PlayerReader   ──► Player(id, name, hp, mana, pos, level, voc...)
        └── CreatureReader ──► [Creature(id, name, hp, pos), ...] (BattleList)
        │
  BotEngine.tick()
        │
        ├── _update_state()    atualiza player + creatures
        │                      sincroniza posição real via BattleList
        │
        ├── _process_events()  emite eventos:
        │                        PLAYER_LOADED
        │                        PLAYER_HEALTH_LOW (< 30%)
        │                        PLAYER_MANA_LOW   (< 20%)
        │                        LEVEL_UP
        │                        CREATURE_DETECTED
        │
        └── _run_scripts()     ScriptEngine.execute_all(context)
                                  ├── HealingScript  (prioridade 100)
                                  ├── BuffScript     (prioridade 50)
                                  └── CavebotScript  (prioridade 30)
                                            │
                                            └── bot_engine.injector
                                                  └── send_key_background(vk)
                                                        └── PostMessage(hwnd,
                                                              WM_KEYDOWN,
                                                              vk, lParam)
```

---

## Cavebot

### Como funciona

1. **Waypoints** são adicionados via UI (grid 3×3 ou entrada manual X/Y/Z)
2. Ao clicar **Ativar Cavebot**, a lista é sincronizada com o `CavebotScript`
3. A cada tick, o script calcula a rota A\* até o próximo waypoint
4. O movimento é enviado via `PostMessage` com o `lParam` correto por tecla
5. Ao chegar no waypoint (tolerância Chebyshev ≤ 2 sqm), avança para o próximo
6. Com `loop: true`, retorna ao waypoint 0 ao completar a rota

### Tipos de waypoint

| Tipo | Descrição |
|---|---|
| `Walk` | Anda normalmente até a posição |
| `Node` | Nó intermediário de rota (sem ação) |
| `Stand` | Para e aguarda no ponto |
| `Rope` | Usa corda (não implementado) |
| `Shovel` | Usa pá (não implementado) |
| `Ladder` | Sobe/desce escada (não implementado) |
| `Use` | Usa item na posição (não implementado) |
| `Lure` | Atrai criaturas (não implementado) |
| `Action` | Ação customizada via `say:exura` |

### Perfis de waypoint

Waypoints são salvos em `.json` em `~/tibia_bot_waypoints/`.

```json
{
  "sections": [
    {
      "name": "Descida",
      "enabled": true,
      "waypoints": [
        {"x": 32335, "y": 31782, "z": 7, "action": "walk"},
        {"x": 32337, "y": 31784, "z": 7, "action": "walk"}
      ]
    }
  ]
}
```

### Anti-stuck

Se o personagem não se mover por `stuck_timeout` segundos (padrão: 8s),
o sistema detecta o stuck, limpa o path atual e tenta recalcular.
Após `stuck_retries` (padrão: 3) tentativas sem sucesso, pula para o próximo waypoint.

---

## Scripts disponíveis

| Script | Prioridade | Descrição |
|---|---|---|
| `HealingScript` | 100 | Cura automática com spell ou poção por % de HP/Mana |
| `BuffScript` | 50 | Lança magias de buff periodicamente |
| `CavebotScript` | 30 | Navegação automática com A\* e anti-stuck |

Todos herdam de `BaseScript` e implementam `execute(context) -> bool`.

```python
# Registrar um script customizado
from src.application.scripts.base_script import BaseScript

class MeuScript(BaseScript):
    def __init__(self):
        super().__init__("MeuScript")
        self.priority = 60

    def execute(self, context):
        player = context["player"]
        bot_engine = context["bot_engine"]
        # ... lógica aqui ...
        return True  # True = executou ação

engine.script_engine.register(MeuScript())
```

---

## Integração UI + BotEngine

Por padrão a UI abre em modo demo (dados zerados, sem leitura de memória).
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

---

## Endereços de memória

Os endereços do cliente Tibia 8.60 ficam em `src/core/constants/addresses_860.py`.

```python
PLAYER = {
    "health":      0x...,
    "max_health":  0x...,
    "mana":        0x...,
    "max_mana":    0x...,
    "level":       0x...,
    "experience":  0x...,
    "name":        0x...,
    "pos_x":       0x...,
    "pos_y":       0x...,
    "pos_z":       0x...,
}
```

> Os endereços variam por servidor. Calibre com Cheat Engine antes de usar
> em OTs diferentes do Kaldrox.

---

## Changelog

### v1.2.0 — 2026-07-27

**Correções críticas de movimento — o boneco agora anda.**

#### `keyboard_injector.py` — BUG-H: `lParam=0` ignorado pelo Tibia 8.60

O `PostMessage(hwnd, WM_KEYDOWN, vk, 0)` com `lParam=0` era **silenciosamente
ignnorado** pelo cliente Tibia 8.60. O cliente verifica o scancode (bits 16-23)
e o extended key flag (bit 24) antes de processar qualquer tecla.

- **Adicionado** `_make_lparam(vk_code, key_up)` que monta o `lParam` correto
- **Setas** (`UP/DOWN/LEFT/RIGHT`) usam `extended=True` (bit 24 setado)
- **Numpad** usa scancodes específicos sem extended bit
- **`WM_KEYUP`** agora inclui bits 30-31 de release corretamente
- **Fallback** via `win32api.MapVirtualKey` para teclas não mapeadas

#### `bot_engine.py` — BUG-G: acesso ao injector encapsulado

- **Adicionado** `@property injector` que retorna `self._injector`
- Scripts deixam de acessar `bot_engine._injector` (atributo privado) diretamente

#### `cavebot_script.py` — BUG-G: uso da property pública

- `_move_player()` agora usa `bot_engine.injector.send_key_background()`
- `_move_towards()` agora usa `bot_engine.injector.send_key_background()`
- `_execute_waypoint_action()` agora usa `bot_engine.injector.cast_spell()`

---

### v1.1.0 — 2026-07-27

- **fix:** `_update_state` estava fora da classe `BotEngine` (bug de indentação)
  causando `AttributeError` silencioso em `tick()`
- **fix:** `_connection_retry_count` e `_max_retry_attempts` não inicializados
- **fix:** import duplicado de `EventManager`/`EventType` removido
- **fix:** `_player_data` (renomeado de `_mock_player`) propagado em todos os arquivos
- **fix:** HP/Mana com clamp — nunca exibe valor maior que o máximo
- **fix:** simulação aleatória de HP removida — dados só mudam com leitura real
- **improvement:** debounce em eventos `PLAYER_HEALTH_LOW` e `PLAYER_MANA_LOW`
- **improvement:** `update_from_engine()` com fallback seguro via `getattr` + `.get()`
- **improvement:** `_start_engine_loop()` com try/except para não silenciar erros
- **improvement:** `gui.py` documentado com instruções de integração
- **docs:** README reescrito com arquitetura, fluxo de dados e exemplos

---

### v1.0.0 — 2026-07-26

- Interface gráfica inicial (Status, Healing, Cavebot, Config)
- Leitura de memória via Win32 API com suporte a processos 32-bit
- MemoryReader com cache TTL
- ProcessManager com fallback `PROCESS_ALL_ACCESS`
- BotEngine com ScriptEngine e EventManager
- Cavebot com A\* pathfinding, anti-stuck e modo follow
- Sistema de perfis de waypoints em JSON por seções

---

## Licença

Este projeto é disponibilizado para fins educacionais e de estudo de engenharia reversa.
O uso em servidores oficiais da CipSoft pode violar os Termos de Serviço.
