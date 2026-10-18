"""Sound (not complete) cycle-parity infeasibility certificates for Bernoulli evidence.

The pairwise constraints are q_ij=P(X_i=1 and X_j=1). For every
simple cycle and odd edge subset F, any joint distribution satisfies
sum_{e in F} d_e - sum_{e not in F} d_e <= |F|-1,
where d_ij=p_i+p_j-2*q_ij. Violation proves global infeasibility;
absence of violation does NOT establish feasibility.

Inputs are interpreted as exact decimal rationals. Bounded to 8 vertices.
"""

from fractions import Fraction


def _rational(value):
    if isinstance(value, bool):
        raise ValueError("boolean is not a probability")
    try:
        number = Fraction(str(value))
    except (ValueError, ZeroDivisionError, TypeError, OverflowError) as exc:
        raise ValueError("probabilities must be finite rational numbers") from exc
    if not 0 <= number <= 1:
        raise ValueError("probabilities must lie in [0,1]")
    return number


def find_cycle_parity_violation(marginals, pairwise, *, max_vertices=8):
    """Return an exact counterexample certificate or None (inconclusive).

    The certificate contains cycle, odd_edges, lhs, rhs. All arithmetic is
    exact rational arithmetic; None is never a global feasibility claim.
    """
    p = tuple(_rational(x) for x in marginals)
    n = len(p)
    if not 1 <= n <= max_vertices or max_vertices > 8:
        raise ValueError("requires 1..8 vertices and max_vertices <= 8")
    if pairwise is None:
        pairwise = {}
    adjacency = [set() for _ in range(n)]
    d = {}
    for key, q_value in pairwise.items():
        if (not isinstance(key, tuple) or len(key) != 2 or
                not all(type(i) is int for i in key)):
            raise ValueError("edges must be (i,j) integer tuples")
        i, j = key
        if not 0 <= i < j < n:
            raise ValueError("edges must satisfy 0 <= i < j < n")
        q = _rational(q_value)
        if not max(Fraction(0), p[i] + p[j] - 1) <= q <= min(p[i], p[j]):
            raise ValueError("edge violates local Frechet bounds")
        d[(i, j)] = p[i] + p[j] - 2*q
        adjacency[i].add(j)
        adjacency[j].add(i)

    def dfs(start, path):
        current = path[-1]
        for nxt in sorted(adjacency[current]):
            if nxt == start:
                if len(path) >= 3 and path[1] < path[-1]:
                    yield tuple(path)
            elif nxt > start and nxt not in path:
                yield from dfs(start, path + (nxt,))

    for start in range(n):
        for cycle in dfs(start, (start,)):
            edges = tuple(tuple(sorted((a, b))) for a, b in
                          zip(cycle, cycle[1:] + cycle[:1]))
            disagreements = tuple(d[edge] for edge in edges)
            for mask in range(1, 1 << len(edges)):
                k = mask.bit_count()
                if k % 2 == 0:
                    continue
                lhs = sum((v if mask & (1 << idx) else -v)
                          for idx, v in enumerate(disagreements))
                rhs = k - 1
                if lhs > rhs:
                    return {
                        "cycle": cycle,
                        "odd_edges": tuple(edges[idx] for idx in range(len(edges))
                                           if mask & (1 << idx)),
                        "lhs": lhs,
                        "rhs": Fraction(rhs),
                    }
    return None
