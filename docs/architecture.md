# Architecture

Bot estruturado em Clean Architecture (adaptada) com três camadas
principais abaixo de `src/`.

## Camadas

```
src/
├── core/                  # dominio puro, sem dependencias de infrastructure
│   ├── entities/          # Player, Creature, Waypoint
│   ├── value_objects/     # Position, Stats, MemoryAddress
│   ├── services/          # TargetingService, HealingService, CombatService, Distance
│   ├── interfaces/        # IMemoryReader, IMemoryWriter, ICommandInjector, IAI
│   ├── constants/         # addresses_860.py, items, spells
│   └── exceptions/        # hierarquia de erros
├── ai/                    # IA: pathfinding (A*), combat, decision, behavior trees
│   ├── pathfinding/       # AStar, Pathfinder, MapAnalyzer
│   ├── combat/            # CombatAI, ThreatAnalyzer, SkillRotation
│   ├── decision/          # DecisionMaker, prioridades
│   └── behavior/          # BehaviorTree, nodes
├── infrastructure/        # adaptadores de IO concretos
│   ├── memory/            # ProcessManager, MemoryReader, MemoryWriter, MemoryCache
│   ├── readers/           # PlayerReader, CreatureReader
│   ├── injection/         # KeyboardInjector (SendInput via win32)
│   └── logging/           # logger
├── application/           # orquestração / use cases
│   ├── bot_engine.py      # loop + estado
│   ├── scripts/           # Healing, Aimbot, Cavebot, Looter
│   ├── events/            # EventManager, EventType, EventHandlers
│   ├── conditions/        # triggers
│   └── use_cases/         # start, stop, connect, cast
└── config/                # Settings + settings.yaml
```

## Fluxo principal

```
main.BotApplication
  └── bot_engine.tick()
       ├── PlayerReader.get_player()
       ├── CreatureReader.get_creatures()
       ├── event_manager.publish(...)
       └── script_engine.execute_all(context)
            ├── HealingScript.execute()
            ├── AimbotScript.execute()
            ├── CavebotScript.execute()
            └── LooterScript.execute()
```

## Decisões

- **IA em `src/ai/`** (não em `src/application/ai/`). `aimbot_script` e
  `cavebot_script` importam de `src.ai.*`; manter uma única árvore.
- **`MemoryAddress` é value object imutável**, com `+`/`-` para operações
  aritméticas em offsets.
- **`EventType` é `str, Enum`** para serialização simples e
  comparação direta.
- **`BotEngine` recebe readers via injeção**, não instancia diretamente.

## Status das fases (README)

| Fase | Estado |
|---|---|
| 1 - Core & Infrastructure | em revisão (Fase 1 do plano de hardening) |
| 2 - Scripts & Events | em revisão (Fase 2 do plano de hardening) |
| 3 - AI & Pathfinding | em revisão (Fase 3 do plano de hardening) |
| UI (PySide6) | não iniciada |
