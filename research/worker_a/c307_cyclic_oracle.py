"""Adversarial cyclic probability constraints, checked against independent LP."""
from __future__ import annotations
import itertools
import json
import random
import numpy as np
from forest_lp_oracle import module, lp_bounds


def moments(n, weights, edges):
    worlds = np.asarray(list(itertools.product((0, 1), repeat=n)), dtype=float)
    marginals = [float(weights @ worlds[:, i]) for i in range(n)]
    pairs = {(i, j): float(weights @ (worlds[:, i] * worlds[:, j])) for i, j in edges}
    return marginals, pairs


def main():
    rng = random.Random(307)
    maximum = 0.0
    counts = {"triangles": 0, "four_cycles": 0, "invalid_triangle_rejected": False}
    for n, edges, iterations in [
        (3, [(0, 1), (0, 2), (1, 2)], 250),
        (4, [(0, 1), (1, 2), (2, 3), (0, 3)], 3),
    ]:
        for _ in range(iterations):
            weights = np.asarray([rng.random() + 1e-3 for _ in range(2**n)])
            weights /= weights.sum()
            marginals, pairs = moments(n, weights, edges)
            got = module.all_fail_bounds(marginals, pairs)
            expected = lp_bounds(marginals, pairs)
            delta = max(abs(a - b) for a, b in zip(got, expected))
            assert delta < 1e-8, (n, got, expected)
            maximum = max(maximum, delta)
            counts["triangles" if n == 3 else "four_cycles"] += 1
    # All three pairwise inputs satisfy Frechet locally, but no global joint exists.
    try:
        module.all_fail_bounds([.1, .1, .1], {(0, 1): 0., (0, 2): .1, (1, 2): .1})
    except ValueError:
        counts["invalid_triangle_rejected"] = True
    assert counts["invalid_triangle_rejected"]
    print(json.dumps({"status": "passed", **counts, "max_abs_error": maximum}, indent=2))


if __name__ == "__main__":
    main()
