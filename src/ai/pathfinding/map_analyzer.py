"""
Análise de mapa e terreno.
"""
from typing import List, Set, Tuple
from src.core.value_objects.position import Position


class MapAnalyzer:
    """Analisa mapa para pathfinding."""
    
    def __init__(self):
        self.known_walkable: Set[Tuple[int, int, int]] = set()
        self.known_blocked: Set[Tuple[int, int, int]] = set()
    
    def mark_walkable(self, position: Position):
        """Marca posição como caminhável."""
        pos_tuple = (position.x, position.y, position.z)
        self.known_walkable.add(pos_tuple)
        if pos_tuple in self.known_blocked:
            self.known_blocked.remove(pos_tuple)
    
    def mark_blocked(self, position: Position):
        """Marca posição como bloqueada."""
        pos_tuple = (position.x, position.y, position.z)
        self.known_blocked.add(pos_tuple)
        if pos_tuple in self.known_walkable:
            self.known_walkable.remove(pos_tuple)
    
    def is_area_safe(
        self,
        center: Position,
        radius: int,
        min_walkable_pct: float = 0.7
    ) -> bool:
        """
        Verifica se área ao redor de center é segura.
        
        Args:
            center: Posição central
            radius: Raio em SQMs
            min_walkable_pct: Porcentagem mínima de tiles caminháveis
            
        Returns:
            True se área é segura
        """
        total_tiles = 0
        walkable_tiles = 0
        
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                pos = Position(center.x + dx, center.y + dy, center.z)
                pos_tuple = (pos.x, pos.y, pos.z)
                
                total_tiles += 1
                
                if pos_tuple in self.known_walkable:
                    walkable_tiles += 1
                elif pos_tuple in self.known_blocked:
                    pass  # Bloqueado, não conta como walkable
                else:
                    # Desconhecido, assume walkable por padrão
                    walkable_tiles += 1
        
        walkable_pct = walkable_tiles / total_tiles if total_tiles > 0 else 0
        return walkable_pct >= min_walkable_pct
    
    def get_walkable_positions(self) -> List[Position]:
        """Retorna todas as posições caminháveis conhecidas."""
        return [Position(x, y, z) for x, y, z in self.known_walkable]
    
    def get_blocked_positions(self) -> List[Position]:
        """Retorna todas as posições bloqueadas conhecidas."""
        return [Position(x, y, z) for x, y, z in self.known_blocked]
