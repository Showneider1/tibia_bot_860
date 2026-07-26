# Memory Scans Research

Coleta de scans de memória feitos durante o desenvolvimento do bot.

## Contexto

Cada scan foi gerado por um utilitário de descoberta de offsets para localizar
campos não documentados em clientes Tibia 8.60 (Kaldrox Otx).

## Arquivos

- `vocation_scan.txt` — varredura da battle list procurando offsets de vocação.
  Resultado: offsets `+80`, `+84` e `+144` retornam valores consistentes em
  criatura/player (2 = Paladin, 1 = Knight).
- `vocation_battlelist_scan.txt` — versão resumida com identificação de processo
  e handle.

## Limitação

O passo de varredura validou parcialmente a estrutura interna das criaturas na
battle list. Para localização completa do player, é necessário mapear os offsets
internos a partir do `MAP_POINTER` (`0x654118`) para a estrutura de mapa do
cliente 8.60.

## Próximos passos

- Descobrir offsets X/Y/Z do player dentro da estrutura apontada por
  `MAP_POINTER`.
- Validar offset `+80` da battle list como indicador confiável de vocação.
