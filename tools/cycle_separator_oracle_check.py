"""Exhaustive oracle cross-check for cycle_inequality_separator on small graphs.

Enumerates simple undirected cycles and all odd edge subsets, then compares the
minimum cycle-inequality slack against the lifted-graph separator.  This is an
independent verifier for small instances, not production code.
"""
from __future__ import annotations

from itertools import combinations, product
from random import Random

from cycle_inequality_separator import separate_cycle_inequality


def simple_cycles(nodes, edges):
    adj = {u: set() for u in nodes}
    for u, v, _ in edges:
        if u == v:
            continue
        adj[u].add(v); adj[v].add(u)
    seen = set()
    out = []
    for s in nodes:
        stack = [(s, [s])]
        while stack:
            u, path = stack.pop()
            for v in adj[u]:
                if v == s and len(path) >= 3:
                    cyc = path[:]
                    rots = []
                    for seq in (cyc, list(reversed(cyc))):
                        for i in range(len(seq)):
                            rots.append(tuple(seq[i:] + seq[:i]))
                    key = min(rots)
                    if key not in seen:
                        seen.add(key); out.append(key)
                elif v not in path and len(path) < len(nodes):
                    stack.append((v, path + [v]))
    return out


def brute_min_cost(nodes, edges):
    weight = {}
    for u, v, d in edges:
        weight[frozenset((u, v))] = d
    best = float("inf")
    for cyc in simple_cycles(nodes, edges):
        ds = [weight[frozenset((cyc[i], cyc[(i+1) % len(cyc)]))] for i in range(len(cyc))]
        for flips in product((0, 1), repeat=len(ds)):
            if sum(flips) % 2:
                cost = sum((1-d) if f else d for d, f in zip(ds, flips))
                best = min(best, cost)
    return best


def check(edges, tol=1e-10):
    nodes = sorted({x for e in edges for x in e[:2]})
    oracle = brute_min_cost(nodes, edges)
    got = separate_cycle_inequality(edges)
    expected = oracle < 1.0 - 1e-12
    assert got.violated == expected, (edges, oracle, got)
    if expected:
        assert abs(got.cost - oracle) <= tol, (edges, oracle, got)


def main():
    rng = Random(20261003)
    # Exhaustive K3 grid: 5^3 = 125 probability assignments.
    vals = (0.0, 0.25, 0.5, 0.75, 1.0)
    for ds in product(vals, repeat=3):
        check([(0,1,ds[0]), (1,2,ds[1]), (2,0,ds[2])])

    # Random K4/K5 instances exercise overlapping cycles and closed-walk reuse.
    for n, trials in ((4, 200), (5, 200)):
        pairs = list(combinations(range(n), 2))
        for _ in range(trials):
            edges = [(u, v, rng.random()) for u, v in pairs]
            check(edges)
    print("oracle cross-check: 525 small instances passed")


if __name__ == "__main__":
    main()
