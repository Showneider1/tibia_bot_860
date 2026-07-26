# Memory and AI Integration

Integração entre leitura de memória (`infrastructure.memory`) e camada
de IA (`ai.combat`).

## Pontos de acoplamento

- `AimbotScript.execute()` consome `src.ai.combat.combat_ai.CombatAI`
  para seleção de alvo e skill rotation.
- `CavebotScript.execute()` consome `src.ai.pathfinding.pathfinder.Pathfinder`
  para calcular rotas.
- `BotEngine` entrega a ambos via `context: dict` com chaves
  `player`, `creatures`, `bot_engine`.

## Estado atual

- `CombatAI` é instanciado lazy dentro de `AimbotScript.execute()`.
- `Pathfinder` é instanciado no `__init__` de `CavebotScript`.

## Próximos passos

- Promotion da inicialização de IA para o `BotEngine` (config-driven).
- Expor telemetria (latência de decisão, cache hit rate) via logging DEBUG.
