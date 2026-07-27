from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """Posição no mapa (x, y, z)."""
    x: int
    y: int
    z: int

    def distance_chebyshev(self, other: "Position") -> int:
        """
        Distância de Chebyshev 3D: max(|dx|, |dy|, |dz|).

        BUG-I CORRIGIDO: versão anterior ignorava o eixo Z,
        retornando apenas max(|dx|, |dy|).

        Impacto do bug:
          - CavebotScript._execute_waypoints(): condição
            'distance <= max_distance_to_waypoint' era satisfeita
            com o player em andar diferente do waypoint (dz != 0
            mas dx=dy=0), fazendo o bot achar que chegou sem mover.
          - AStar.heuristic(): subestimava custo de rotas multi-andar,
            gerando paths com custo incorreto.
          - CavebotScript._find_nearest_index(): nós em outros andares
            eram considerados 'próximos' (distância <= 1), causando
            reset do path no andar errado.

        A correção inclui dz no cálculo, tornando o comportamento
        correto tanto para movimento 2D (mesmo andar, dz=0, sem
        impacto) quanto para rotas com mudança de andar.
        """
        return max(abs(self.x - other.x), abs(self.y - other.y), abs(self.z - other.z))

    def same_floor(self, other: "Position") -> bool:
        return self.z == other.z
