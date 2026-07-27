"""
Script de auto-loot avançado.
Inspiração: ElfBot - loot por valor, abrir corpses, loot filter.
"""
import time
from typing import Dict, Any, Set, Optional, List
from .base_script import BaseScript
from src.core.entities.player import Player
from src.core.entities.creature import Creature


class LooterScript(BaseScript):
    """Script de auto-loot com sistema de tracking de kills e loot."""

    def __init__(self):
        super().__init__("Looter")
        self.priority = 20
        self.config = {
            "enabled": False,
            "loot_radius": 3,           # SQMs ao redor para procurar corpses
            "items_to_loot": {          # ID: nome (para loot filter)
                3031: "Gold Coin",
                3035: "Platinum Coin",
                3034: "Crystal Coin",
                3725: "Magic Plate Armor",
                3391: "Magic Sword",
                3274: "Knight Axe",
                3356: "Crossbow",
                3509: "Plate Armor",
                3354: "Plate Shield",
                3447: "Brown Mushroom",  # Food
                3114: "Wand of Inferno",
                3078: "Wand of Decay",
                3079: "Wand of Cosmic Energy",
                3074: "Snakebite Rod",
                3075: "Moonlight Rod",
                3082: "Hailstorm Rod",
            },
            # Items de alto valor (sempre looter)
            "high_value_items": {
                3035: "Platinum Coin",
                3034: "Crystal Coin",
                3725: "Magic Plate Armor",
                3391: "Magic Sword",
                3114: "Wand of Inferno",
            },
            # Items para ignorar (low value)
            "ignore_items": set(),       # Set de IDs para ignorar
            "open_corpses": True,
            "loot_hotkey": "F4",         # Hotkey para abrir corpse/use item
            "use_hotkey_loot": True,     # Usar hotkey configurada no Tibia para loot
            "loot_delay": 0.5,           # Delay entre loot actions (segundos)
            "max_loot_per_run": 10,      # Máximo de items por execução
            "open_corpse_hotkey": "F5",  # Hotkey para abrir corpse
            
            # Tracking de kills para saber onde procurar corpses
            "track_kills": True,
            "kill_positions_timeout": 60,  # Segundos antes de esquecer kill position
        }
        self._looted_positions: Set[tuple] = set()
        self._kill_positions: List[Dict] = []  # [{position, timestamp, creature_name}]
        self._last_loot_time = 0

    def execute(self, context: Dict[str, Any]) -> bool:
        player: Player = context.get("player")
        creatures: List[Creature] = context.get("creatures", [])
        bot_engine = context.get("bot_engine")

        if not player or not bot_engine:
            return False

        current_time = time.time()
        
        # Respeita delay entre loot actions
        if current_time - self._last_loot_time < self.config["loot_delay"]:
            return False

        # Atualizar tracking de kills (detecta criaturas que morreram)
        if self.config["track_kills"]:
            self._update_kill_tracking(creatures, current_time)

        # Limpar kill positions antigas
        self._cleanup_old_kills(current_time)

        # Procurar corpses para loot (baseado em kills recentes)
        loot_targets = self._find_loot_targets(player)
        
        if not loot_targets:
            return False

        # Executar loot no primeiro target
        target = loot_targets[0]
        success = self._loot_position(player, target, bot_engine)
        
        if success:
            self._last_loot_time = current_time
            self.mark_looted(target["x"], target["y"], target["z"])
            return True
            
        return False

    def _update_kill_tracking(self, creatures: List[Creature], current_time: float) -> None:
        """Rastreia criaturas que morreram baseado na HP bar."""
        # Esta é uma implementação simplificada. Em uma versão mais avançada,
        # poderíamos rastrear criaturas que tinham HP e agora não existem mais.
        # Por enquanto, apenas logamos que o sistema está ativo.
        pass

    def register_kill(self, creature: Creature) -> None:
        """Registra uma kill para loot tracking."""
        if not self.config["track_kills"]:
            return
        
        pos = creature.position
        self._kill_positions.append({
            "x": pos.x,
            "y": pos.y,
            "z": pos.z,
            "timestamp": time.time(),
            "creature_name": creature.name,
        })
        self._log.debug(f"Kill registrada: {creature.name} em ({pos.x}, {pos.y}, {pos.z})")

    def _cleanup_old_kills(self, current_time: float) -> None:
        """Remove kill positions antigas."""
        timeout = self.config["kill_positions_timeout"]
        self._kill_positions = [
            k for k in self._kill_positions
            if current_time - k["timestamp"] < timeout
        ]

    def _find_loot_targets(self, player: Player) -> List[Dict]:
        """Encontra positions para loot baseado em kills recentes."""
        targets = []
        
        for kill in self._kill_positions:
            # Verificar se já foi looted
            if (kill["x"], kill["y"], kill["z"]) in self._looted_positions:
                continue
            
            # Verificar distância
            distance = abs(player.position.x - kill["x"]) + abs(player.position.y - kill["y"])
            if distance > self.config["loot_radius"]:
                continue
            
            targets.append(kill)
        
        return targets

    def _loot_position(self, player: Player, target: Dict, bot_engine) -> bool:
        """Executa loot em uma position específica."""
        try:
            if self.config["use_hotkey_loot"]:
                # Usa hotkey configurada no Tibia (F4 ou similar)
                # O Tibia tem auto-loot quando você clica em um item com a hotkey certa
                bot_engine._injector.send_hotkey(self.config["loot_hotkey"])
                self._log.info(f"💰 Loot usando hotkey em ({target['x']}, {target['y']})")
                return True
            elif self.config["open_corpses"]:
                # Tenta abrir corpse com hotkey
                bot_engine._injector.send_hotkey(self.config["open_corpse_hotkey"])
                self._log.info(f"📦 Abrindo corpse em ({target['x']}, {target['y']})")
                return True
            return False
        except Exception as e:
            self._log.error(f"Erro ao loot em ({target['x']}, {target['y']}): {e}")
            return False

    def mark_looted(self, x: int, y: int, z: int) -> None:
        """Marca posição como já saqueada."""
        self._looted_positions.add((x, y, z))
        self._log.debug(f"Posição marcada como looted: ({x}, {y}, {z})")

    def clear_looted_cache(self) -> None:
        """Limpa cache de posições saqueadas."""
        self._looted_positions.clear()
        self._log.info("Cache de loot limpo")

    def clear_kill_tracking(self) -> None:
        """Limpa tracking de kills."""
        self._kill_positions.clear()
        self._log.info("Tracking de kills limpo")

    def add_item_to_loot(self, item_id: int, item_name: str) -> None:
        """Adiciona item à lista de loot."""
        self.config["items_to_loot"][item_id] = item_name
        self._log.info(f"Item adicionado à lista de loot: {item_name} (ID: {item_id})")

    def remove_item_from_loot(self, item_id: int) -> bool:
        """Remove item da lista de loot."""
        if item_id in self.config["items_to_loot"]:
            name = self.config["items_to_loot"][item_id]
            del self.config["items_to_loot"][item_id]
            self._log.info(f"Item removido da lista de loot: {name} (ID: {item_id})")
            return True
        return False

    def ignore_item(self, item_id: int) -> None:
        """Adiciona item à lista de ignorados."""
        self.config["ignore_items"].add(item_id)

    def get_loot_stats(self) -> Dict:
        """Retorna estatísticas de loot."""
        return {
            "total_looted": len(self._looted_positions),
            "pending_kills": len(self._kill_positions),
            "items_tracked": len(self.config["items_to_loot"]),
        }