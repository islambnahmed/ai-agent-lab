"""Independent LP falsification of the exact forest dependence formula.

Optional research dependencies: numpy, scipy. Not imported by production code.
Run: python tools/research/forest_lp_crosscheck.py
"""
from itertools import product
import numpy as np
from scipy.optimize import linprog


def forest_bounds(marginals, edges):
    n = len(marginals)
    parent = list(range(n))

    def find(v):
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    for i, j in edges:
        a, b = find(i), find(j)
        if a == b:
            raise ValueError("not a forest")
        parent[a] = b

    components = {}
    for i in range(n):
        components.setdefault(find(i), []).append(i)
    lows, highs = [], []
    for nodes in components.values():
        es = [(i, j, q) for (i, j), q in edges.items()
              if i in nodes and j in nodes]
        if not es:
            lows.append(marginals[nodes[0]])
            highs.append(marginals[nodes[0]])
        else:
            degree = {i: 0 for i in nodes}
            for i, j, _ in es:
                degree[i] += 1
                degree[j] += 1
            lows.append(max(0., sum(q for _, _, q in es) -
                            sum((degree[i] - 1) * marginals[i] for i in nodes)))
            highs.append(min(q for _, _, q in es))
    return max(0., sum(lows) - (len(lows) - 1)), min(highs)


def lp_bounds(n, marginals, edges):
    worlds = list(product((0, 1), repeat=n))
    A = np.array([[1.] * len(worlds)] +
                 [[float(w[i]) for w in worlds] for i in range(n)] +
                 [[float(w[i] and w[j]) for w in worlds] for i, j in edges],
                 float)
    b = np.array([1.] + list(marginals) + list(edges.values()), float)
    c = np.array([float(all(w)) for w in worlds])
    lo = linprog(c, A_eq=A, b_eq=b, bounds=(0, None), method="highs")
    hi = linprog(-c, A_eq=A, b_eq=b, bounds=(0, None), method="highs")
    if not (lo.success and hi.success):
        raise AssertionError((lo.message, hi.message))
    return lo.fun, -hi.fun


def test(seed=6419, cases=150):
    rng = np.random.default_rng(seed)
    worst = 0.
    checked = 0
    for n in (3, 4, 5, 6):
        worlds = list(product((0, 1), repeat=n))
        for case in range(cases):
            mass = rng.dirichlet(np.ones(2 ** n) *
                                 rng.choice([.1, .3, 1., 3.]))
            marg = [sum(mass[k] for k, w in enumerate(worlds) if w[i])
                    for i in range(n)]
            edges = {}
            for j in range(1, n):
                if rng.random() < .75:
                    i = int(rng.integers(0, j))
                    edges[(i, j)] = sum(
                        mass[k] for k, w in enumerate(worlds)
                        if w[i] and w[j])
            got = forest_bounds(marg, edges)
            want = lp_bounds(n, marg, edges)
            diff = max(abs(a - b) for a, b in zip(got, want))
            worst = max(worst, diff)
            if diff > 2e-7:
                raise AssertionError((n, case, got, want, diff))
            checked += 1
    print(f"PASS: {checked} feasible forest instances, n=3..6; "
          f"max absolute difference {worst:.3g}")


if __name__ == "__main__":
    test()
