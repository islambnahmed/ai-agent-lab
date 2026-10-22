"""Independent differential oracle for forest failure-probability bounds.

Run from the repository root (research-only optional dependencies):
    python -m pip install numpy scipy
    python research/worker_a/forest_lp_oracle.py

The oracle enumerates all 2**n Bernoulli worlds and optimizes P(all fail)
using SciPy HiGHS; it does not reuse the production forest formula.
No network I/O or external side effects at execution.
"""
from __future__ import annotations
import importlib.util
import itertools
import json
import random
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "tools" / "dependence_bounds.py"
spec = importlib.util.spec_from_file_location("lab_dependence_bounds", MODULE)
if spec is None or spec.loader is None:
    raise RuntimeError("Cannot load lab dependence bounds module")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def lp_bounds(marginals: list[float], pairs: dict[tuple[int, int], float]):
    """Optimize all-failure mass with only atom nonnegativity and observed moments."""
    n = len(marginals)
    worlds = np.asarray(list(itertools.product((0, 1), repeat=n)), dtype=float)
    rows = [np.ones(2**n)] + [worlds[:, i] for i in range(n)]
    rhs = [1.0] + marginals
    for (i, j), joint in pairs.items():
        rows.append(worlds[:, i] * worlds[:, j])
        rhs.append(joint)
    target = np.prod(worlds, axis=1)
    constraints = np.asarray(rows)
    lower = linprog(target, A_eq=constraints, b_eq=rhs, bounds=(0, None), method="highs")
    upper = linprog(-target, A_eq=constraints, b_eq=rhs, bounds=(0, None), method="highs")
    if not lower.success or not upper.success:
        raise AssertionError(f"Feasible generated distribution rejected: {lower.message}; {upper.message}")
    return lower.fun, -upper.fun


def random_forest_case(rng: random.Random, n: int):
    """Sample a complete joint law, then expose a random acyclic subset of edges."""
    weights = np.asarray([rng.random() + 1e-4 for _ in range(2**n)])
    weights /= weights.sum()
    worlds = np.asarray(list(itertools.product((0, 1), repeat=n)), dtype=float)
    p = [float(weights @ worlds[:, i]) for i in range(n)]
    pairs = {}
    # At most one earlier parent per child guarantees an acyclic graph.
    for child in range(1, n):
        if rng.random() < .8:
            parent = rng.randrange(child)
            pairs[(parent, child)] = float(weights @ (worlds[:, parent] * worlds[:, child]))
    return p, pairs


def main():
    rng = random.Random(306)
    max_error = 0.0
    worst = None
    cases = 0
    for n in (3, 4, 5, 6):
        for sample_id in range(150):
            marginals, pairs = random_forest_case(rng, n)
            actual = module.all_fail_bounds(marginals, pairs)
            oracle = lp_bounds(marginals, pairs)
            error = max(abs(a-b) for a, b in zip(actual, oracle))
            if error > max_error:
                max_error = error
                worst = {"n": n, "sample": sample_id, "actual": actual, "oracle": oracle}
            if error > 1e-8:
                raise AssertionError(f"Oracle mismatch at n={n}, sample={sample_id}: {actual} != {oracle}")
            cases += 1
    for n in (3, 4, 5, 6):
        marginals = [.5] * n
        pairs = {(i-1, i): .5 for i in range(1, n)}
        assert module.all_fail_bounds(marginals, pairs) == (.5, .5)
        oracle = lp_bounds(marginals, pairs)
        assert max(abs(x-.5) for x in oracle) < 1e-8
        cases += 1
    try:
        module.all_fail_bounds([.1, .1], {(0, 1): .2})
    except ValueError:
        pass
    else:
        raise AssertionError("Impossible edge accepted")
    print(json.dumps({"status": "passed", "seed": 306, "feasible_cases": cases,
                      "random_cases": 600, "boundary_cases": 4,
                      "max_abs_error": max_error, "worst": worst,
                      "note": "Finite differential check; not a formal proof or market evidence"}, indent=2))


if __name__ == "__main__":
    main()
