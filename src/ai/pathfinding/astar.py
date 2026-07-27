"""
Implementacao do algoritmo A* para pathfinding.

BUG-A CORRIGIDO: is_walkable() tinha logica invertida.
Quando walkable_tiles estava vazio (situacao normal - o bot nao
pre-popula o mapa do Tibia), todos os vizinhos eram bloqueados
e o A* retornava None silenciosamente.

Ordem correta:
  1. blocked_tiles -> sempre False
  2. walkable_tiles populado -> restringe a eles
  3. walkable_tiles vazio -> free-walk (padrao Tibia 8.60)
"""
from typing import List, Optional, Tuple, Set
from src.core.value_objects.position import Position
import heapq


class Node:
    """No para A*."""

    def __init__(self, position: Position, parent: Optional['Node'] = None):
        self.position = position
        self.parent = parent
        self.g = 0  # Custo do inicio ate este no
        self.h = 0  # Heuristica (estimativa ate o fim)
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
        """Define tiles caminhavels."""
        self.walkable_tiles = {(p.x, p.y, p.z) for p in positions}

    def add_blocked(self, position: Position) -> None:
        """Adiciona tile bloqueada."""
        self.blocked_tiles.add((position.x, position.y, position.z))

    def is_walkable(self, position: Position) -> bool:
        """
        Verifica se posicao e caminhavel.

        BUG-A FIX - ordem correta dos checks:
          ANTES (quebrado):
            if self.walkable_tiles:
                return pos in walkable AND pos not in blocked
            return pos not in blocked
          -> Quando walkable_tiles era populado com qualquer coisa,
             qualquer posicao fora da lista retornava False, bloqueando
             todos os vizinhos do A*.

          AGORA (correto):
            1. Blocked sempre tem prioridade (False).
            2. Se walkable_tiles definido -> restringe a eles.
            3. Se vazio -> free-walk (assume tudo caminhavel).
        """
        pos_tuple = (position.x, position.y, position.z)

        # Regra 1: bloqueado explicitamente -> sempre False
        if pos_tuple in self.blocked_tiles:
            return False

        # Regra 2: se temos mapa definido, restringe a tiles validos
        if self.walkable_tiles:
            return pos_tuple in self.walkable_tiles

        # Regra 3: sem mapa populado -> free-walk (padrao Tibia 8.60)
        return True

    def heuristic(self, a: Position, b: Position) -> int:
        """Heuristica: distancia Chebyshev."""
        return a.distance_chebyshev(b)

    def get_neighbors(self, position: Position) -> List[Position]:
        """Retorna vizinhos validos (8 direcoes)."""
        neighbors = []

        directions = [
            (0, -1, 0),   # N
            (0,  1, 0),   # S
            (1,  0, 0),   # E
            (-1, 0, 0),   # W
            (1, -1, 0),   # NE
            (-1,-1, 0),   # NW
            (1,  1, 0),   # SE
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
        Encontra caminho de start ate goal usando A*.

        Returns:
            Lista de posicoes (caminho) ou None se nao encontrar
        """
        start_node = Node(start)
        open_list  = []
        closed_set = set()

        heapq.heappush(open_list, start_node)
        iterations = 0

        while open_list and iterations < max_iterations:
            iterations += 1
            current = heapq.heappop(open_list)
            closed_set.add(current)

            if current.position == goal:
                return self._reconstruct_path(current)

            for neighbor_pos in self.get_neighbors(current.position):
                neighbor = Node(neighbor_pos, current)

                if neighbor in closed_set:
                    continue

                dx = abs(neighbor_pos.x - current.position.x)
                dy = abs(neighbor_pos.y - current.position.y)
                is_diagonal = dx == 1 and dy == 1

                neighbor.g = current.g + (14 if is_diagonal else 10)
                neighbor.h = self.heuristic(neighbor_pos, goal) * 10
                neighbor.f = neighbor.g + neighbor.h

                should_add = True
                for open_node in open_list:
                    if open_node == neighbor and open_node.g <= neighbor.g:
                        should_add = False
                        break

                if should_add:
                    heapq.heappush(open_list, neighbor)

        return None

    def _reconstruct_path(self, node: Node) -> List[Position]:
        """Reconstroi caminho do objetivo ate o inicio."""
        path = []
        current = node
        while current is not None:
            path.append(current.position)
            current = current.parent
        return list(reversed(path))
