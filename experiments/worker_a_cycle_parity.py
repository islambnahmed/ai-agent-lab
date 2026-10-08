"""Exact necessary cycle-parity checks for Bernoulli pairwise feasibility.

A cycle has an even number of disagreements in every binary assignment.
For any odd subset F of cycle edges, disagreement probabilities
d_e=P(X_u != X_v) obey sum(d_e in F)-sum(d_e not in F) <= |F|-1.

A strict violation proves infeasibility. Passing the check never proves
cyclic feasibility. Forest certificates come from the existing fast path.
"""
from fractions import Fraction
import math

try:
    from .worker_a_forest_feasibility import assess_forest_feasibility
except ImportError:
    from worker_a_forest_feasibility import assess_forest_feasibility


def strongest_odd_subset_violation(disagreements):
    """Return (exact maximum inequality violation, odd edge-index subset).

    Parity DP avoids enumerating 2**(k-1) odd subsets on a k-edge cycle.
    """
    d = [Fraction(x) for x in disagreements]
    even, odd = (Fraction(0), ()), None
    for i, value in enumerate(d):
        gain = 2 * value - 1
        even_candidates = [even]
        odd_candidates = [(even[0] + gain, even[1] + (i,))]
        if odd is not None:
            even_candidates.append((odd[0] + gain, odd[1] + (i,)))
            odd_candidates.append(odd)
        even = max(even_candidates, key=lambda item: item[0])
        odd = max(odd_candidates, key=lambda item: item[0])
    if odd is None:
        raise ValueError("cycle must contain at least one edge")
    return 1 - sum(d) + odd[0], odd[1]


class _SearchBudgetExceeded(Exception):
    pass


def _simple_cycles(adjacency, max_cycle_length, max_search_steps):
    """Yield each undirected simple cycle once; bound DFS expansions."""
    steps = 0
    for start in range(len(adjacency)):
        def walk(path, visited):
            nonlocal steps
            steps += 1
            if steps > max_search_steps:
                raise _SearchBudgetExceeded
            current = path[-1]
            for neighbor in adjacency[current]:
                if neighbor == start:
                    if len(path) >= 3 and path[1] < path[-1]:
                        yield tuple(path)
                elif neighbor > start and neighbor not in visited and len(path) < max_cycle_length:
                    yield from walk(path + [neighbor], visited | {neighbor})
        yield from walk([start], {start})


def assess_cycle_parity(marginals, edges, *, tol=1e-12,
                        max_cycles=10000, max_cycle_length=12,
                        max_search_steps=200000):
    """Conservative status: feasible (forest), infeasible, or inconclusive.

    Infeasible requires a strict exact parity violation > tol, or a hard
    invalid/local constraint from the forest checker. Exhausting a budget
    never implies feasibility.
    """
    if not isinstance(max_cycles, int) or isinstance(max_cycles, bool) or max_cycles < 1:
        raise ValueError("max_cycles must be a positive integer")
    if (not isinstance(max_cycle_length, int) or isinstance(max_cycle_length, bool)
            or max_cycle_length < 3):
        raise ValueError("max_cycle_length must be an integer >= 3")
    if (not isinstance(max_search_steps, int) or isinstance(max_search_steps, bool)
            or max_search_steps < 1):
        raise ValueError("max_search_steps must be a positive integer")
    if not math.isfinite(tol) or tol < 0:
        raise ValueError("tol must be finite and nonnegative")

    edges = list(edges)
    baseline = assess_forest_feasibility(marginals, edges, tol=tol)
    if baseline["status"] != "inconclusive":
        return {**baseline, "cycles_checked": 0}

    nodes = list(marginals)
    ids = {node: i for i, node in enumerate(nodes)}
    adjacency = [set() for _ in nodes]
    disagreement = {}
    for u, v, q in edges:
        # The forest checker has already validated edge structure.
        i, j = ids[u], ids[v]
        adjacency[i].add(j)
        adjacency[j].add(i)
        disagreement[frozenset((i, j))] = (
            Fraction(marginals[u]) + Fraction(marginals[v]) - 2 * Fraction(q)
        )

    count, near_violations = 0, 0
    try:
        for cycle in _simple_cycles(adjacency, max_cycle_length, max_search_steps):
            if count >= max_cycles:
                return {"status": "inconclusive", "reason": "cycle budget exhausted",
                        "cycles_checked": count, "truncated": True,
                        "near_violations": near_violations}
            count += 1
            pairs = [(cycle[i], cycle[(i + 1) % len(cycle)]) for i in range(len(cycle))]
            d = [disagreement[frozenset(pair)] for pair in pairs]
            violation, odd_indices = strongest_odd_subset_violation(d)
            if violation > Fraction(tol):
                return {"status": "infeasible",
                        "reason": "exact cycle parity inequality violated",
                        "cycle": [nodes[i] for i in cycle],
                        "odd_subset_edges": [tuple(nodes[v] for v in pairs[i]) for i in odd_indices],
                        "violation_exact": str(violation), "cycles_checked": count}
            if violation > 0:
                near_violations += 1
    except _SearchBudgetExceeded:
        return {"status": "inconclusive", "reason": "DFS search budget exhausted",
                "cycles_checked": count, "truncated": True,
                "near_violations": near_violations}

    return {"status": "inconclusive",
            "reason": "cycle inequalities are necessary, not sufficient; no global feasibility certificate",
            "cycles_checked": count, "near_violations": near_violations,
            "length_limit_may_omit_cycles": len(nodes) > max_cycle_length}
