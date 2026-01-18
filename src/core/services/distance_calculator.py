from src.core.entities.player import Player
from src.core.entities.creature import Creature


def distance_player_to_creature(player: Player, creature: Creature) -> int:
    """Distância Chebyshev entre player e criatura."""
    return player.position.distance_chebyshev(creature.position)
