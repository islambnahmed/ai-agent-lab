"""Polynomial-time separator for binary cycle parity inequalities.

Given an undirected graph with disagreement probabilities d_e in [0,1], find
an odd-parity closed walk of cost < 1 in the standard two-layer lift. Such a
walk certifies a violated cycle inequality (and can be decomposed to a simple
violated cycle). This is a necessary-condition oracle, not a general global
feasibility solver.
"""
from __future__ import annotations

from dataclasses import dataclass
from heapq import heappop, heappush
from math import inf
from typing import Hashable, Iterable

Node = Hashable
Edge = tuple[Node, Node, float]


@dataclass(frozen=True)
class SeparationResult:
    violated: bool
    cost: float = inf
    walk: tuple[tuple[Node, Node, int], ...] = ()
    reason: str = ""


def separate_cycle_inequality(
    edges: Iterable[Edge], *, tol: float = 1e-12
) -> SeparationResult:
    """Return a violated odd-parity walk when minimum lifted cost is < 1."""
    edge_list = list(edges)
    adj: dict[Node, list[tuple[Node, float]]] = {}
    for u, v, d in edge_list:
        if d < -tol or d > 1.0 + tol:
            return SeparationResult(False, reason=f"invalid disagreement probability: {d}")
        d = min(1.0, max(0.0, d))
        adj.setdefault(u, []).append((v, d))
        adj.setdefault(v, []).append((u, d))

    best = SeparationResult(False)
    for start in adj:
        source = (start, 0)
        target = (start, 1)
        dist = {source: 0.0}
        prev: dict[tuple[Node, int], tuple[tuple[Node, int], int]] = {}
        heap = [(0.0, 0, source)]
        serial = 1

        while heap:
            du, _, state = heappop(heap)
            if du != dist.get(state):
                continue
            if state == target:
                break
            u, layer = state
            for v, d in adj[u]:
                for flip, weight in ((0, d), (1, 1.0 - d)):
                    nxt = (v, layer ^ flip)
                    nd = du + weight
                    if nd + tol < dist.get(nxt, inf):
                        dist[nxt] = nd
                        prev[nxt] = (state, flip)
                        heappush(heap, (nd, serial, nxt))
                        serial += 1

        cost = dist.get(target, inf)
        if cost + tol < best.cost:
            walk_rev: list[tuple[Node, Node, int]] = []
            cur = target
            while cur != source:
                old, flip = prev[cur]
                walk_rev.append((old[0], cur[0], flip))
                cur = old
            best = SeparationResult(
                cost < 1.0 - tol,
                cost,
                tuple(reversed(walk_rev)),
                "odd-parity lifted closed walk" if cost < 1.0 - tol else "",
            )

    return best


def _self_test() -> None:
    # Deterministic odd anticorrelation triangle violates with cost zero.
    r = separate_cycle_inequality([("a","b",1),("b","c",1),("c","a",1)])
    assert r.violated and abs(r.cost) < 1e-12
    assert sum(f for _,_,f in r.walk) % 2 == 1

    # Deterministic even anticorrelation square has no strict violation.
    r = separate_cycle_inequality([
        ("a","b",1),("b","c",1),("c","d",1),("d","a",1)
    ])
    assert not r.violated and r.cost >= 1.0 - 1e-12

    # A soft inconsistent triangle: three d=0.9 edges -> odd cost 0.3.
    r = separate_cycle_inequality([("a","b",.9),("b","c",.9),("c","a",.9)])
    assert r.violated and abs(r.cost - .3) < 1e-12

    # Boundary is strict: a two-edge backtrack can attain exactly 1, not violate.
    r = separate_cycle_inequality([("a","b",.2)])
    assert not r.violated


if __name__ == "__main__":
    _self_test()
    print("cycle inequality separator self-test: ok")
