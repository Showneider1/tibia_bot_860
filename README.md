# Tibia Bot 8.60

Bot para Tibia 8.60 (cliente/custom OT) com leitura de memória, injeção de
comandos via SendInput, motor de scripts e IA de pathfinding/combate.

## Status atual

| Camada | Estado |
|---|---|
| Leitura de memória (memória protegida via `ReadProcessMemory`) | funcional, com cache TTL |
| Entity Layer (Player, Creature, Waypoint) | populadas |
| Scripts (Healing, Aimbot, Cavebot, Looter) | populados |
| Eventos (`EventManager` + `EventType` + handlers) | populados |
| AI (A*, Behavior Tree, Combat AI, Threat Analyzer, Decision Maker) | populado em `src/ai/` |
| UI (PySide6) | não implementada |

## Requisitos

- Python 3.10+
- Windows (necessário para `pywin32`, `keyboard`, `pyautogui`)
- Cliente Tibia 8.60 (ou compatível) — configuração padrão assume
  `Kaldrox Client_BR Old.exe`

## Instalação

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

> Em Linux/macOS, apenas `psutil`, `pyyaml` e o tooling de dev rodam; os
> adaptadores Windows permanecem fora.

## Configuração

Toda a configuração vive em `src/config/settings.yaml`. Edite esse
arquivo para:

- apontar para o `.exe` correto do cliente (`game.process_name`,
  `game.window_title`);
- ajustar thresholds de healing / aimbot;
- configurar scripts de cave/loot.

A classe `src.config.settings.Settings` carrega esse arquivo e
expõe dot-access (`settings.get("scripts.healing.hp_threshold")`).

## Uso

### Modo interativo (recomendado para debug)

```bash
python -m src.main
```

Comandos disponíveis dentro do REPL: `start`, `stop`, `status`, `exit`.

### Exemplo: scripts registrados

```bash
python examples/bot_with_scripts.py
```

Carrega `HealingScript`, `AimbotScript`, `CavebotScript`, `LooterScript`,
registra handlers de eventos e abre a janela do cliente (certifique-se
de que o Tibia está em execução e logado).

### Exemplo: testes de IA (pathfinding, BT, decisão)

```bash
python examples/test_phase3.py
```

Cobre A*, Threat Analyzer, Behavior Tree e Decision Maker sem
precisar de cliente conectado.

## Arquitetura

Veja `docs/architecture.md` para o diagrama de camadas (core, ai,
infrastructure, application, config).

## Endereços de memória

Veja `docs/memory_addresses.md` para a tabela de offsets
(player, battle list, criaturas, map pointer). Os scans parciais estão
em `docs/research/`.

## Hotkeys

- `insert` — habilita/desabilita o bot
- `end` — parada de emergência
- `Ctrl+C` — encerra o processo

## Troubleshooting

- **`ModuleNotFoundError: src.X.Y`** — execute comandos a partir da
  raiz do projeto (onde vive `src/`).
- **Janela do cliente não encontrada** — confirme
  `game.window_title` em `settings.yaml` (substring, case-insensitive).
- **HP retornando zero** — Tibia provavelmente não está logado;
  PlayerReader retorna `None` quando `id == 0`.
- **Pathfinding lento** — habilite cache no `Pathfinder` e/ou aumente
  `ai.pathfinding.max_iterations`.

## Licença

MIT.
