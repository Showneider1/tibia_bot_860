"""
Implementação do algoritmo A* para pathfinding.
"""
from typing import List, Optional, Tuple, Set
from src.core.value_objects.position import Position
import heapq


class Node:
    """Nó para A*."""
    
    def __init__(self, position: Position, parent: Optional['Node'] = None):
        self.position = position
        self.parent = parent
        self.g = 0  # Custo do início até este nó
        self.h = 0  # Heurística (estimativa até o fim)
        self.f = 0  # g + h
    
    def __lt__(self, other):
        return self.f < other.f
    
    def __eq__(self, other):
        return self.position == other.position
    
    def __hash__(self):
        return hash((self.position.x, self.position.y, self.position.z))


class AStar:
    """Algoritmo A* para pathfinding."""
    
    def __init__(self):
        self.walkable_tiles: Set[Tuple[int, int, int]] = set()
        self.blocked_tiles: Set[Tuple[int, int, int]] = set()
    
    def set_walkable(self, positions: List[Position]) -> None:
        """Define tiles caminháveis."""
        self.walkable_tiles = {(p.x, p.y, p.z) for p in positions}
    
    def add_blocked(self, position: Position) -> None:
        """Adiciona tile bloqueada."""
        self.blocked_tiles.add((position.x, position.y, position.z))
    
    def is_walkable(self, position: Position) -> bool:
        """Verifica se posição é caminhável."""
        pos_tuple = (position.x, position.y, position.z)
        
        # Se temos walkable_tiles definido, usa apenas eles
        if self.walkable_tiles:
            return pos_tuple in self.walkable_tiles and pos_tuple not in self.blocked_tiles
        
        # Senão, apenas verifica se não está bloqueado
        return pos_tuple not in self.blocked_tiles
    
    def heuristic(self, a: Position, b: Position) -> int:
        """Heurística: distância Chebyshev."""
        return a.distance_chebyshev(b)
    
    def get_neighbors(self, position: Position) -> List[Position]:
        """Retorna vizinhos válidos (8 direções)."""
        neighbors = []
        
        # 8 direções: N, S, E, W, NE, NW, SE, SW
        directions = [
            (0, -1, 0),   # N
            (0, 1, 0),    # S
            (1, 0, 0),    # E
            (-1, 0, 0),   # W
            (1, -1, 0),   # NE
            (-1, -1, 0),  # NW
            (1, 1, 0),    # SE
            (-1, 1, 0),   # SW
        ]
        
        for dx, dy, dz in directions:
            new_pos = Position(
                position.x + dx,
                position.y + dy,
                position.z + dz
            )
            
            if self.is_walkable(new_pos):
                neighbors.append(new_pos)
        
        return neighbors
    
    def find_path(
        self,
        start: Position,
        goal: Position,
        max_iterations: int = 1000
    ) -> Optional[List[Position]]:
        """
        Encontra caminho de start até goal usando A*.
        
        Returns:
            Lista de posições (caminho) ou None se não encontrar
        """
        start_node = Node(start)
        goal_node = Node(goal)
        
        open_list = []
        closed_set = set()
        
        heapq.heappush(open_list, start_node)
        iterations = 0
        
        while open_list and iterations < max_iterations:
            iterations += 1
            
            # Pega nó com menor f
            current = heapq.heappop(open_list)
            closed_set.add(current)
            
            # Chegou no objetivo?
            if current.position == goal:
                return self._reconstruct_path(current)
            
            # Explora vizinhos
            for neighbor_pos in self.get_neighbors(current.position):
                neighbor = Node(neighbor_pos, current)
                
                if neighbor in closed_set:
                    continue
                
                # Calcula custos
                # Diagonal custa mais (aproximadamente √2 ≈ 1.4)
                dx = abs(neighbor_pos.x - current.position.x)
                dy = abs(neighbor_pos.y - current.position.y)
                is_diagonal = dx == 1 and dy == 1
                
                neighbor.g = current.g + (14 if is_diagonal else 10)
                neighbor.h = self.heuristic(neighbor_pos, goal) * 10
                neighbor.f = neighbor.g + neighbor.h
                
                # Verifica se já existe um caminho melhor
                should_add = True
                for i, open_node in enumerate(open_list):
                    if open_node == neighbor and open_node.g <= neighbor.g:
                        should_add = False
                        break
                
                if should_add:
                    heapq.heappush(open_list, neighbor)
        
        # Não encontrou caminho
        return None
    
    def _reconstruct_path(self, node: Node) -> List[Position]:
        """Reconstrói caminho do objetivo até o início."""
        path = []
        current = node
        
        while current is not None:
            path.append(current.position)
            current = current.parent
        
        return list(reversed(path))
