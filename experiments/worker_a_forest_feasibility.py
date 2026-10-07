"""Certified fast-path for Bernoulli pairwise-constraint feasibility on forests.

Given marginals p_i and edge joints q_ij=P(X_i=1,X_j=1), local Frechet
feasibility is sufficient for global feasibility whenever the constraint graph
is a forest. Cyclic graphs are *inconclusive*, not infeasible.
"""

import math
from fractions import Fraction

def frechet_bounds(p, r):
    return max(0.0, p - (1.0 - r)), min(p, r)

def assess_forest_feasibility(marginals, edges, tol=1e-12):
    """Return a conservative structural feasibility assessment.

    edges: iterable of (u, v, q). Result status is one of:
      feasible  -- graph is a forest and all local constraints are valid
      infeasible -- a marginal/edge violates probability/Frechet constraints
      inconclusive -- graph contains a cycle or a constraint only passes
                      due to floating-point tolerance (not a certificate)

    `tol` only distinguishes hard violations from near-boundary ambiguity;
    it never relaxes the conditions for a "feasible" certificate.
    """
    if not math.isfinite(tol) or tol < 0:
        raise ValueError("tol must be finite and nonnegative")
    near_boundary_violation = False
    exact_tol = Fraction(tol)
    for node, p in marginals.items():
        if not math.isfinite(p):
            return {"status": "infeasible", "reason": f"marginal {node!r} is non-finite"}
        if not (0.0 <= p <= 1.0):
            if p < -tol or p > 1.0 + tol:
                return {"status": "infeasible", "reason": f"marginal {node!r} outside [0,1]"}
            near_boundary_violation = True

    parent = {x: x for x in marginals}
    rank = {x: 0 for x in marginals}
    cyclic = False

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        nonlocal cyclic
        ra, rb = find(a), find(b)
        if ra == rb:
            cyclic = True
            return
        if rank[ra] < rank[rb]:
            ra, rb = rb, ra
        parent[rb] = ra
        if rank[ra] == rank[rb]:
            rank[ra] += 1

    seen_pairs = set()
    for u, v, q in edges:
        if u not in marginals or v not in marginals:
            return {"status": "infeasible", "reason": "edge references missing marginal"}
        if u == v:
            return {"status": "infeasible", "reason": "self-edge is not a pairwise constraint"}
        pair = frozenset((u, v))
        if pair in seen_pairs:
            return {"status": "infeasible", "reason": "duplicate edge is ambiguous"}
        seen_pairs.add(pair)
        if not math.isfinite(q):
            return {"status": "infeasible", "reason": f"edge {(u, v)!r} has non-finite joint probability"}
        # Compare exact rational values of the supplied finite numbers.
        # Floating-point addition can round a violated Frechet bound to a tie.
        pu, pv, joint = Fraction(marginals[u]), Fraction(marginals[v]), Fraction(q)
        lo_exact, hi_exact = max(Fraction(0), pu + pv - 1), min(pu, pv)
        if joint < lo_exact or joint > hi_exact:
            if joint < lo_exact - exact_tol or joint > hi_exact + exact_tol:
                lo, hi = frechet_bounds(marginals[u], marginals[v])
                return {"status": "infeasible", "reason": f"edge {(u, v)!r} violates Frechet bounds [{lo}, {hi}]"}
            near_boundary_violation = True
        union(u, v)

    if near_boundary_violation:
        return {"status": "inconclusive", "reason": "one or more constraints pass only within tolerance; no exact feasibility certificate"}
    if cyclic:
        return {"status": "inconclusive", "reason": "cycle present; global feasibility check required"}
    return {"status": "feasible", "reason": "forest plus local Frechet feasibility certifies a global joint distribution"}
