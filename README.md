# 🎮 Tibia Bot 8.60 - AI Powered

Bot inteligente para Tibia 8.60 com arquitetura escalável, IA avançada, pathfinding A* e sistema de scripts modular.

## ✨ Features

### ✅ Fase 1 - Core & Infrastructure
- ✅ Leitura/escrita de memória otimizada com cache
- ✅ Process Manager com detecção automática
- ✅ Keyboard Injector (SendInput, PostMessage)
- ✅ Event System completo
- ✅ Logging profissional com rotação de arquivos
- ✅ Entities: Player, Creature, Waypoint
- ✅ Value Objects: Position, Stats, Address
- ✅ Services: Targeting, Healing, Combat

### ✅ Fase 2 - Scripts & Events
- ✅ Script Engine com prioridades
- ✅ HealingBot (healing inteligente multi-spell)
- ✅ AimBot (auto-attack com targeting)
- ✅ CaveBot (navegação automática)
- ✅ Looter (auto-loot)
- ✅ Event Handlers customizáveis
- ✅ Conditions & Triggers

### ✅ Fase 3 - AI & Pathfinding
- ✅ Algoritmo A* para pathfinding
- ✅ Map Analyzer (análise de terreno)
- ✅ Threat Analyzer (análise de ameaças)
- ✅ Skill Rotation por vocação
- ✅ Combat AI (decisões inteligentes)
- ✅ Behavior Trees (Selector, Sequence, Action)
- ✅ Decision Maker (sistema de prioridades)

## 🚀 Instalação

### Requisitos
- Python 3.11+
- Windows (para acesso à memória)
- Tibia 8.60 (ou servidor customizado compatível)

### Passo a Passo

1. **Clone o repositório:**
```bash
git clone https://github.com/yourusername/tibia-bot-860.git
cd tibia-bot-860
Crie ambiente virtual:

bash
python -m venv venv
venv\Scripts\activate
Instale dependências:

bash
pip install -r requirements.txt
Configure:

bash
cp config.yaml config.local.yaml
# Edite config.local.yaml conforme necessário
📖 Uso
Modo Básico (Leitura de Memória)
bash
python src/main.py
Com Scripts (Healing + AimBot)
bash
python examples/test_phase2.py
Com AI (Pathfinding + Combat AI)
bash
python examples/test_phase3.py