from src.core.entities.player import Player


class HealingService:
    """Serviço de decisão de cura básica (sem IA ainda)."""

    def needs_heal(self, player: Player, threshold_percent: int) -> bool:
        return player.hp_percent() < threshold_percent and player.is_alive()

    def can_heal(self, player: Player, min_mana: int) -> bool:
        return player.stats.mana >= min_mana
