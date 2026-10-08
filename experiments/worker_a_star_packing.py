"""Necessary 3-leaf star Bonferroni inequalities for binary pairwise marginals.

For center c and leaves a,b,d, with all six pairwise joints supplied:
    p_c >= q_ca + q_cb + q_cd - q_ab - q_ad - q_bd.
Proof: A_i={X_c=1,X_i=1} are subsets of {X_c=1}. The second-order
Bonferroni lower bound for their union, and
P(A_i intersection A_j) <= P(X_i=1,X_j=1), give the inequality.

Passing these inequalities never certifies cyclic feasibility.
"""

from fractions import Fraction
from itertools import combinations
import math

try:
    from .worker_a_cycle_parity import assess_cycle_parity
except ImportError:
    from worker_a_cycle_parity import assess_cycle_parity


def assess_star_packing(marginals, edges, *, tol=1e-12, max_triplets=100000,
                        **cycle_options):
    """Add sound 3-leaf star infeasibility tests to the cycle-parity check."""
    if not isinstance(max_triplets, int) or isinstance(max_triplets, bool) or max_triplets < 1:
        raise ValueError("max_triplets must be a positive integer")
    if not math.isfinite(tol) or tol < 0:
        raise ValueError("tol must be finite and nonnegative")
    edges = list(edges)
    baseline = assess_cycle_parity(marginals, edges, tol=tol, **cycle_options)
    if baseline["status"] != "inconclusive":
        return {**baseline, "star_triplets_checked": 0}

    # The baseline validates edge endpoints, duplicates and finite values.
    joints = {frozenset((u, v)): Fraction(q) for u, v, q in edges}
    neighbors = {node: set() for node in marginals}
    for u, v, _ in edges:
        neighbors[u].add(v)
        neighbors[v].add(u)
    exact_tol = Fraction(tol)
    checked, near_violations = 0, 0
    for center in marginals:
        leaves = [node for node in marginals if node in neighbors[center]]
        for a, b, d in combinations(leaves, 3):
            if any(frozenset(pair) not in joints for pair in ((a, b), (a, d), (b, d))):
                continue
            if checked >= max_triplets:
                return {"status": "inconclusive", "reason": "star-triplet search budget exhausted",
                        "star_triplets_checked": checked, "star_truncated": True,
                        "star_near_violations": near_violations, "cycle_baseline": baseline}
            checked += 1
            violation = (joints[frozenset((center, a))]
                         + joints[frozenset((center, b))]
                         + joints[frozenset((center, d))]
                         - joints[frozenset((a, b))]
                         - joints[frozenset((a, d))]
                         - joints[frozenset((b, d))]
                         - Fraction(marginals[center]))
            if violation > exact_tol:
                return {"status": "infeasible",
                        "reason": "exact 3-leaf star Bonferroni inequality violated",
                        "center": center, "leaves": [a, b, d],
                        "violation_exact": str(violation),
                        "star_triplets_checked": checked, "cycle_baseline": baseline}
            if violation > 0:
                near_violations += 1
    return {**baseline, "star_triplets_checked": checked,
            "star_near_violations": near_violations}
