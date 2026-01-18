"""
Interface principal de pathfinding.
"""
from typing import List, Optional
from src.core.value_objects.position import Position
from .astar import AStar
from src.infrastructure.logging.logger import get_logger


class Pathfinder:
    """Pathfinder principal com cache e otimizações."""
    
    def __init__(self):
        self.astar = AStar()
        self._log = get_logger("Pathfinder")
        self._path_cache = {}
        self.max_cache_size = 100
    
    def find_path(
        self,
        start: Position,
        goal: Position,
        use_cache: bool = True
    ) -> Optional[List[Position]]:
        """
        Encontra caminho de start para goal.
        
        Args:
            start: Posição inicial
            goal: Posição objetivo
            use_cache: Usar cache de caminhos
            
        Returns:
            Lista de posições ou None
        """
        # Verifica cache
        cache_key = (start, goal)
        if use_cache and cache_key in self._path_cache:
            self._log.debug(f"Caminho encontrado no cache: {start} → {goal}")
            return self._path_cache[cache_key]
        
        # Calcula caminho
        self._log.debug(f"Calculando caminho: {start} → {goal}")
        path = self.astar.find_path(start, goal)
        
        if path:
            self._log.debug(f"Caminho encontrado com {len(path)} passos")
            
            # Adiciona ao cache
            if use_cache:
                self._cache_path(cache_key, path)
        else:
            self._log.warning(f"Nenhum caminho encontrado de {start} para {goal}")
        
        return path
    
    def _cache_path(self, key, path):
        """Adiciona caminho ao cache."""
        if len(self._path_cache) >= self.max_cache_size:
            # Remove primeiro item (FIFO)
            self._path_cache.pop(next(iter(self._path_cache)))
        
        self._path_cache[key] = path
    
    def clear_cache(self):
        """Limpa cache de caminhos."""
        self._path_cache.clear()
    
    def set_walkable_area(self, positions: List[Position]):
        """Define área caminhável."""
        self.astar.set_walkable(positions)
    
    def add_obstacle(self, position: Position):
        """Adiciona obstáculo."""
        self.astar.add_blocked(position)
        self.clear_cache()  # Invalida cache
