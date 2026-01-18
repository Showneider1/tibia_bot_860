from typing import List
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.core.value_objects.combat_mode import CombatMode
from src.infrastructure.logging.logger import get_logger


def distance_player_to_creature(player: Player, creature: Creature) -> int:
    """Distância Chebyshev entre player e criatura."""
    return player.position.distance_chebyshev(creature.position)


class TargetingService:
    """Serviço de seleção de alvo (estilo Elfbot)."""

    def __init__(self):
        self._log = get_logger("TargetingService")

    def select_target(
        self,
        player: Player,
        creatures: List[Creature],
        mode: CombatMode,
        max_distance: int = 7,
    ) -> Creature | None:
        if not creatures:
            return None

        valid = []
        for c in creatures:
            # LOG DE DEBUG - mostra por que cada criatura foi filtrada
            if not c.visible:
                self._log.debug(f"    ✗ {c.name}: não visível")
                continue
            
            if not player.position.same_floor(c.position):
                self._log.debug(f"    ✗ {c.name}: andar diferente (Player Z:{player.position.z} vs Creature Z:{c.position.z})")
                continue
            
            dist = distance_player_to_creature(player, c)
            if dist > max_distance:
                self._log.debug(f"    ✗ {c.name}: muito longe (dist: {dist} > max: {max_distance})")
                continue
            
            if not c.is_alive():
                self._log.debug(f"    ✗ {c.name}: morto (HP: {c.stats.health})")
                continue
            
            self._log.debug(f"    ✓ {c.name}: VÁLIDO (dist: {dist}, HP: {c.stats.health})")
            valid.append(c)

        if not valid:
            return None

        if mode == CombatMode.LOWEST_HP:
            return min(valid, key=lambda c: c.stats.health)
        if mode == CombatMode.CLOSEST:
            return min(valid, key=lambda c: distance_player_to_creature(player, c))
        if mode == CombatMode.HIGHEST_THREAT:
            return max(valid, key=lambda c: c.stats.health)

        return valid[0]
