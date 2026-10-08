"""Sound but incomplete signed binary-cardinality infeasibility certificates.

For any fully observed clique S, flip an arbitrary subset of Bernoulli
variables, Y_i = X_i or 1-X_i.  K = sum(Y_i) is integer-valued, so
Var(K) >= frac(E[K]) * (1-frac(E[K])).

A positive witness certifies infeasibility; None is always inconclusive.
The caller should validate marginal and pairwise probability ranges first.
No third-party dependencies.
"""
from itertools import combinations
from math import floor, fsum
from sys import float_info


def signed_cardinality_witness(marginals, pairwise, *, max_subset_size=6,
                               max_large_flips=2, max_cliques=20000,
                               tolerance=1e-12):
    """Return first violating witness, or None if search is inconclusive.

    Search signed fully-observed cliques of sizes 3..max_subset_size,
    subject to max_cliques. Also search the full graph when complete,
    using at most max_large_flips for n > max_subset_size.

    Complementary sign assignments have identical variance gaps; on small
    cliques we fix the first variable unflipped. The large-clique search is
    deliberately incomplete and its default costs O(n^2).
    """
    n = len(marginals)
    if max_subset_size < 3 or max_large_flips < 0 or max_cliques < 0:
        raise ValueError("invalid search budget")
    p = tuple(map(float, marginals))
    neighbors = [set() for _ in range(n)]
    for i, j in pairwise:
        if not (0 <= i < j < n):
            raise ValueError("pairwise keys must satisfy 0 <= i < j < n")
        neighbors[i].add(j)
        neighbors[j].add(i)

    def check(subset, large=False):
        m = len(subset)
        mu0 = fsum(p[i] for i in subset)
        cov = {}
        rows = {i: 0.0 for i in subset}
        diagonal = fsum(p[i] * (1.0 - p[i]) for i in subset)
        for i, j in combinations(subset, 2):
            c = float(pairwise[(i, j)]) - p[i] * p[j]
            cov[(i, j)] = c
            rows[i] += c
            rows[j] += c
        variance0 = diagonal + 2.0 * fsum(cov.values())
        # Account conservatively for cancellation in finite precision.
        slack = max(tolerance, 64.0 * float_info.epsilon * m * m)
        if large:
            flips_iter = (f for k in range(min(max_large_flips, m) + 1)
                          for f in combinations(subset, k))
        else:
            flips_iter = (f for k in range(m)
                          for f in combinations(subset[1:], k))
        for flips in flips_iter:
            mu = mu0 + fsum(1.0 - 2.0 * p[i] for i in flips)
            variance = (variance0
                        - 4.0 * fsum(rows[i] for i in flips)
                        + 8.0 * fsum(cov[(i, j)]
                                     for i, j in combinations(flips, 2)))
            fraction = mu - floor(mu)
            lower = fraction * (1.0 - fraction)
            gap = lower - variance
            if gap > slack:
                return {
                    "subset": tuple(subset), "flipped": tuple(flips),
                    "mean": mu, "variance": variance,
                    "integer_variance_lower": lower,
                    "violation": gap,
                    "tolerance_used": slack,
                }
        return None

    if n < 3:
        return None
    complete = all(len(neighbors[i]) == n - 1 for i in range(n))
    if complete:
        witness = check(tuple(range(n)), large=n > max_subset_size)
        if witness is not None:
            return witness
    examined = 0
    limit = min(max_subset_size, n)

    def expand(prefix, candidates):
        nonlocal examined
        if examined >= max_cliques:
            return None
        if len(prefix) >= 3:
            # The full graph was already checked when n <= limit.
            if not (complete and len(prefix) == n):
                examined += 1
                witness = check(prefix)
                if witness is not None:
                    return witness
        if len(prefix) >= limit:
            return None
        for pos, v in enumerate(candidates):
            if examined >= max_cliques:
                return None
            witness = expand(prefix + (v,),
                             [u for u in candidates[pos + 1:]
                              if u in neighbors[v]])
            if witness is not None:
                return witness
        return None

    return expand((), list(range(n)))
