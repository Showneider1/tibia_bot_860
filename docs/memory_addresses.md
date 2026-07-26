# Memory Addresses — Tibia 8.60

Endereços canônicos do cliente 8.60. Fonte primária:
[TibiaAPI 8.60 Vectors](https://github.com/ianobermiller/tibiaapi/blob/master/tibiaapi/Addresses/Versions/Version860.cs).

## Player

Base: `Player.Experience = 0x63FE8C`

| Campo | Endereço | Offset (relativo a `0x63FE8C`) |
|---|---|---|
| experience | 0x63FE8C | 0 |
| level | 0x63FE88 | -4 |
| magic_level | 0x63FE84 | -8 |
| health | 0x63FE94 | +8 |
| health_max | 0x63FE90 | +4 |
| mana | 0x63FE6C | -20 |
| mana_max | 0x63FE68 | -24 |
| soul | 0x63FE64 | -28 |
| stamina | 0x63FE60 | -32 |
| capacity | 0x63FE5C | -36 |
| id | 0x63FE98 | +12 |
| level_percent | 0x63FE80 | -12 |
| magic_percent | 0x63FE7C | -16 |
| flags (vocação) | 0x63FE24 | -108 |
| goto_x | 0x63FEDC | +80 |
| goto_y | 0x63FED8 | +76 |
| goto_z | 0x63FED4 | +72 |

## Battle List

| Campo | Valor |
|---|---|
| start | 0x63FEF8 |
| step (bytes por criatura) | 0xA8 (168) |
| max creatures | 250 |

## Creature Offsets (dentro da struct da battle list)

| Campo | Offset (relativo à base do slot) |
|---|---|
| id | 0 |
| name | 4 |
| x | 36 |
| y | 40 |
| z | 44 |
| walking | 76 |
| direction | 80 |
| hp_bar | 136 |
| walk_speed | 140 |
| visible | 144 |

## Map / Misc

| Campo | Endereço |
|---|---|
| MAP_POINTER | 0x654118 |
| Login account | 0x79CF04 |
| Login password | 0x79CEE4 |

## Vocações (índice extraído de `flags` ou offset `+80` da BL)

| Índice | Vocação |
|---|---|
| 0 | None |
| 1 | Knight |
| 2 | Paladin |
| 3 | Sorcerer |
| 4 | Druid |
| 5 | Elite Knight |
| 6 | Royal Paladin |
| 7 | Master Sorcerer |
| 8 | Elder Druid |

## Estado do scan

Validação concreta disponível em `research/vocation_scan.txt` e
`research/vocation_battlelist_scan.txt`. Resultados parciais:
- Battle list offset `+80` → 2 (Paladin)
- Battle list offset `+84` → 2 (Paladin)
- Battle list offset `+144` → 1 (Knight)

Offsets internos a partir de `MAP_POINTER` ainda não mapeados.
