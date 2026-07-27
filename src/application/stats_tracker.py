"""
Sistema de tracking de estatísticas e HUD (Head-Up Display).
Inspirado em ElfBot - mostra HP%, mana%, XP/h, gold/h, stamina, etc.
"""
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from src.core.entities.player import Player
from src.core.entities.creature import Creature
from src.infrastructure.logging.logger import get_logger


@dataclass
class SessionStats:
    """Estatísticas da sessão de caça."""
    start_time: float = field(default_factory=time.time)
    start_experience: int = 0
    start_level: int = 0
    
    # Tracking
    kills: int = 0
    loot_collected: int = 0
    gold_gained: int = 0
    
    # Damage tracking
    damage_dealt: int = 0
    damage_taken: int = 0
    heals_cast: int = 0
    mana_used: int = 0
    
    # Timing
    last_experience: int = 0
    last_experience_update: float = field(default_factory=time.time)
    last_level: int = 0
    
    # Combat
    creatures_killed: Dict[str, int] = field(default_factory=dict)  # name -> count
    
    # Survival
    deaths: int = 0
    times_low_hp: int = 0
    
    # Movement
    distance_traveled: int = 0
    last_position: Optional[tuple] = None


class StatsTracker:
    """Tracker de estatísticas do bot para HUD e relatórios."""
    
    def __init__(self):
        self._log = get_logger("StatsTracker")
        self._stats = SessionStats()
        self._running = False
    
    def start_session(self, player: Player) -> None:
        """Inicia uma nova sessão de tracking."""
        self._stats = SessionStats(
            start_time=time.time(),
            start_experience=player.experience,
            start_level=player.level,
            last_experience=player.experience,
            last_level=player.level,
        )
        self._running = True
        self._log.info("📊 Sessão de tracking iniciada")
    
    def update(self, player: Player, creatures: List[Creature]) -> None:
        """Atualiza estatísticas com dados atuais do player e criaturas."""
        if not self._running or not player:
            return
        
        current_time = time.time()
        
        # Atualiza experiência ganha
        if player.experience > self._stats.last_experience:
            exp_gained = player.experience - self._stats.last_experience
            self._stats.last_experience = player.experience
            self._stats.last_experience_update = current_time
        
        # Detecta level up
        if player.level > self._stats.last_level:
            self._stats.last_level = player.level
            self._log.info(f"📈 Level Up! Agora level {player.level}")
        
        # Detecta mortes (HP foi para 0 ou muito baixo)
        if player.stats.health <= 0:
            self._stats.deaths += 1
            self._log.warning(f"💀 Morte detectada! Total: {self._stats.deaths}")
        elif player.hp_percent() < 10:
            self._stats.times_low_hp += 1
        
        # Atualiza distância viajada
        current_pos = (player.position.x, player.position.y, player.position.z)
        if self._stats.last_position and self._stats.last_position != current_pos:
            # Calcula distância Chebyshev aproximada
            dx = abs(current_pos[0] - self._stats.last_position[0])
            dy = abs(current_pos[1] - self._stats.last_position[1])
            self._stats.distance_traveled += max(dx, dy)
        self._stats.last_position = current_pos
    
    def register_kill(self, creature: Creature) -> None:
        """Registra uma kill."""
        self._stats.kills += 1
        name = creature.name
        if name not in self._stats.creatures_killed:
            self._stats.creatures_killed[name] = 0
        self._stats.creatures_killed[name] += 1
    
    def register_heal(self, spell_name: str) -> None:
        """Registra um heal."""
        self._stats.heals_cast += 1
    
    def register_loot(self, item_id: int, item_name: str, gold_value: int = 0) -> None:
        """Registra loot coletado."""
        self._stats.loot_collected += 1
        if gold_value > 0:
            self._stats.gold_gained += gold_value
    
    def get_xp_per_hour(self) -> float:
        """Calcula XP por hora."""
        elapsed = time.time() - self._stats.start_time
        if elapsed <= 0:
            return 0
        
        xp_gained = self._stats.last_experience - self._stats.start_experience
        return (xp_gained / elapsed) * 3600
    
    def get_gold_per_hour(self) -> float:
        """Calcula gold ganho por hora."""
        elapsed = time.time() - self._stats.start_time
        if elapsed <= 0:
            return 0
        
        return (self._stats.gold_gained / elapsed) * 3600
    
    def get_kills_per_hour(self) -> float:
        """Calcula kills por hora."""
        elapsed = time.time() - self._stats.start_time
        if elapsed <= 0:
            return 0
        
        return (self._stats.kills / elapsed) * 3600
    
    def get_time_to_level(self) -> Optional[float]:
        """Calcula tempo estimado para próximo level (em horas)."""
        xp_per_hour = self.get_xp_per_hour()
        if xp_per_hour <= 0:
            return None
        
        # Estimativa: se level X precisa ~ X * X * 100 XP
        # (fórmula aproximada do Tibia)
        next_level_xp = self._stats.last_level * self._stats.last_level * 100
        current_xp_rate = xp_per_hour
        
        # Se ainda não ganhou XP, usa estimativa
        if self._stats.last_experience <= self._stats.start_experience:
            return None
        
        return next_level_xp / current_xp_rate
    
    def get_session_time(self) -> float:
        """Retorna tempo de sessão em horas."""
        return (time.time() - self._stats.start_time) / 3600
    
    def get_stats_summary(self) -> Dict[str, Any]:
        """Retorna resumo completo de estatísticas."""
        return {
            "session_time_hours": self.get_session_time(),
            "xp_per_hour": self.get_xp_per_hour(),
            "gold_per_hour": self.get_gold_per_hour(),
            "kills_per_hour": self.get_kills_per_hour(),
            "total_kills": self._stats.kills,
            "total_loot": self._stats.loot_collected,
            "total_gold": self._stats.gold_gained,
            "total_heals": self._stats.heals_cast,
            "deaths": self._stats.deaths,
            "times_low_hp": self._stats.times_low_hp,
            "distance_traveled": self._stats.distance_traveled,
            "creatures_killed": dict(self._stats.creatures_killed),
        }
    
    def get_hud_text(self) -> str:
        """Gera texto formatado para HUD."""
        stats = self.get_stats_summary()
        
        hud_lines = [
            "╔══════════════════════════════════╗",
            "║        📊 HUNT STATS            ║",
            "╠══════════════════════════════════╣",
            f"║ ⏱️  Tempo: {stats['session_time_hours']:.2f}h          ║",
            f"║ ⚡ XP/h:  {stats['xp_per_hour']:>10,}       ║",
            f"║ 💰 Gold/h: {stats['gold_per_hour']:>8,}       ║",
            f"║ 🗡️  Kills/h: {stats['kills_per_hour']:>8.1f}    ║",
            f"║ 💀 Total Kills: {stats['total_kills']:>5}       ║",
            f"║ 💊 Heals: {stats['total_heals']:>5}              ║",
            f"║ 🚶 Distance: {stats['distance_traveled']:>5} sqm       ║",
            "╠══════════════════════════════════╣",
            f"║ ⚠️  Deaths: {stats['deaths']} | Low HP: {stats['times_low_hp']}   ║",
            "╚══════════════════════════════════╝",
        ]
        
        return "\n".join(hud_lines)
    
    def print_stats(self) -> None:
        """Imprime estatísticas no log."""
        self._log.info("\n" + self.get_hud_text())
        
        # Mostra top creatures killed
        if self._stats.creatures_killed:
            self._log.info("\n🎯 Creatures Killed:")
            sorted_kills = sorted(self._stats.creatures_killed.items(), 
                                  key=lambda x: x[1], reverse=True)[:5]
            for name, count in sorted_kills:
                self._log.info(f"  {name}: {count}")
    
    def reset(self) -> None:
        """Reseta estatísticas."""
        self._running = False
        self._stats = SessionStats()
        self._log.info("Estatísticas resetadas")
    
    def stop_session(self) -> None:
        """Para a sessão e imprime resumo final."""
        if self._running:
            self._running = False
            self._log.info("📊 Sessão finalizada")
            self.print_stats()


# Singleton para fácil acesso
_stats_tracker: Optional[StatsTracker] = None


def get_stats_tracker() -> StatsTracker:
    """Retorna instância singleton do StatsTracker."""
    global _stats_tracker
    if _stats_tracker is None:
        _stats_tracker = StatsTracker()
    return _stats_tracker