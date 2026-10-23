"""Opt-in exact bounds from integer counts sharing one population.

This API avoids binary-float feasibility ambiguities by using Fraction.
Supported graphs: disconnected components that are isolated vertices, trees,
or complete three-node triangles. Other cyclic components are unsupported.
"""
from fractions import Fraction
from numbers import Integral


def _count(x, total, label):
    if isinstance(x, bool) or not isinstance(x, Integral) or not 0 <= x <= total:
        raise ValueError(f"{label} must be an integer count in [0,total]")
    return Fraction(int(x), total)


def all_fail_bounds_from_counts(total, marginal_counts, pairwise_counts=None):
    """Return exact (Fraction lower, upper) bounds on all modes failing.

    All counts must refer to the same positive integer population total.
    This checks mathematical consistency, not empirical provenance.
    """
    if isinstance(total, bool) or not isinstance(total, Integral) or total <= 0:
        raise ValueError("total must be a positive integer")
    if not marginal_counts:
        raise ValueError("at least one mode is required")
    n = len(marginal_counts)
    p = [_count(x, total, f"marginal[{i}]") for i, x in enumerate(marginal_counts)]
    raw = pairwise_counts if pairwise_counts is not None else {}
    q = {}
    for edge, count in raw.items():
        if not isinstance(edge, tuple) or len(edge) != 2:
            raise ValueError("pairwise keys must be (i,j) tuples")
        i, j = edge
        if any(isinstance(v, bool) or not isinstance(v, Integral) for v in (i, j)) or not 0 <= i < j < n:
            raise ValueError("pairwise keys must have 0 <= i < j < n")
        v = _count(count, total, f"pairwise[{i},{j}]")
        if v < max(Fraction(0), p[i] + p[j] - 1) or v > min(p[i], p[j]):
            raise ValueError("pairwise count violates exact Frechet bounds")
        q[i, j] = v
    if not q:
        return max(Fraction(0), sum(p) - (n - 1)), min(p)

    # Solve each connected component independently, then couple their
    # all-fail events by Frechet bounds. A triangle can coexist with trees,
    # isolated vertices, or other disjoint triangles.
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i, j in q:
        parent[find(i)] = find(j)
    components = {}
    for v in range(n):
        components.setdefault(find(v), []).append(v)

    lowers, uppers = [], []
    for nodes in components.values():
        s = set(nodes)
        edges = [(i, j, v) for (i, j), v in q.items() if i in s and j in s]
        if not edges:
            lo = hi = p[nodes[0]]
        elif len(edges) == len(nodes) - 1:
            # Every connected, simple graph with |V|-1 edges is a tree.
            deg = {v: 0 for v in nodes}
            for i, j, _ in edges:
                deg[i] += 1
                deg[j] += 1
            lo = max(Fraction(0), sum(v for _, _, v in edges) -
                     sum((deg[v] - 1) * p[v] for v in nodes))
            hi = min(v for _, _, v in edges)
        elif len(nodes) == 3 and len(edges) == 3:
            a, b, c = sorted(nodes)
            ab, ac, bc = q[a, b], q[a, c], q[b, c]
            lo = max(Fraction(0), ab + ac - p[a], ab + bc - p[b],
                     ac + bc - p[c])
            hi = min(ab, ac, bc,
                     1 - p[a] - p[b] - p[c] + ab + ac + bc)
            if lo > hi:
                raise ValueError("pairwise counts are globally infeasible")
        else:
            raise NotImplementedError(
                "exact-count API supports tree and complete-triangle components")
        lowers.append(lo)
        uppers.append(hi)

    return max(Fraction(0), sum(lowers) - (len(lowers) - 1)), min(uppers)


def any_survives_bounds_from_counts(total, marginal_counts, pairwise_counts=None):
    """Exact bounds on the probability at least one mode survives."""
    lo, hi = all_fail_bounds_from_counts(total, marginal_counts, pairwise_counts)
    return 1 - hi, 1 - lo
