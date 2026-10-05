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
from math import inf, isfinite
from typing import Hashable, Iterable

Node = Hashable
Edge = tuple[Node, Node, float]


@dataclass(frozen=True)
class SeparationResult:
    violated: bool
    cost: float = inf
    walk: tuple[tuple[Node, Node, int], ...] = ()
    simple_cycle: tuple[tuple[Node, Node, int], ...] = ()
    reason: str = ""


def _odd_simple_cycle(
    walk: tuple[tuple[Node, Node, int], ...]
) -> tuple[tuple[Node, Node, int], ...]:
    """Decompose an odd closed walk to an odd simple cycle.

    Repeated vertices split a closed walk into two closed subwalks. Because the
    parent has odd flip parity, exactly one child is odd; recursively retaining
    that child terminates at a cycle with no repeated internal vertex.
    """
    current = walk
    if not current or sum(flip for _, _, flip in current) % 2 != 1:
        raise ValueError("expected a non-empty odd-parity closed walk")

    while True:
        vertices = [current[0][0]] + [v for _, v, _ in current]
        if vertices[-1] != vertices[0]:
            raise ValueError("walk is not closed")

        first: dict[Node, int] = {}
        split: tuple[int, int] | None = None
        for idx, vertex in enumerate(vertices[:-1]):
            if vertex in first:
                split = (first[vertex], idx)
                break
            first[vertex] = idx

        if split is None:
            return current

        i, j = split
        inside = current[i:j]
        outside = current[j:] + current[:i]
        current = (
            inside
            if sum(f for _, _, f in inside) % 2 == 1
            else outside
        )


def separate_cycle_inequality(
    edges: Iterable[Edge], *, tol: float = 1e-12
) -> SeparationResult:
    """Return a violated odd-parity walk when minimum lifted cost is < 1."""
    edge_list = list(edges)
    adj: dict[Node, list[tuple[Node, float]]] = {}
    seen_edges: set[frozenset[Node]] = set()
    for u, v, d in edge_list:
        if u == v:
            return SeparationResult(False, reason="self-loops are not supported")
        key = frozenset((u, v))
        if key in seen_edges:
            return SeparationResult(False, reason="parallel undirected edges are not supported")
        seen_edges.add(key)
        if not isfinite(d):
            return SeparationResult(False, reason=f"invalid disagreement probability: {d}")
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
            walk = tuple(reversed(walk_rev))
            violated = cost < 1.0 - tol
            best = SeparationResult(
                violated,
                cost,
                walk,
                _odd_simple_cycle(walk) if violated else (),
                "odd-parity lifted closed walk" if violated else "",
            )

    return best


def _self_test() -> None:
    # Deterministic odd anticorrelation triangle violates with cost zero.
    r = separate_cycle_inequality([("a","b",1),("b","c",1),("c","a",1)])
    assert r.violated and abs(r.cost) < 1e-12
    assert sum(f for _,_,f in r.walk) % 2 == 1
    assert r.simple_cycle
    verts = [r.simple_cycle[0][0]] + [v for _,v,_ in r.simple_cycle]
    assert verts[0] == verts[-1] and len(set(verts[:-1])) == len(verts) - 1

    # Deterministic even anticorrelation square has no strict violation.
    r = separate_cycle_inequality([
        ("a","b",1),("b","c",1),("c","d",1),("d","a",1)
    ])
    assert not r.violated and r.cost >= 1.0 - 1e-12

    # A soft inconsistent triangle: three d=0.9 edges -> odd cost 0.3.
    r = separate_cycle_inequality([("a","b",.9),("b","c",.9),("c","a",.9)])
    assert r.violated and abs(r.cost - .3) < 1e-12

    # Non-finite probabilities are invalid and must never be silently clamped.
    for bad in (float("nan"), float("inf"), float("-inf")):
        r = separate_cycle_inequality([("a","b",bad)])
        assert not r.violated and r.reason.startswith("invalid disagreement probability")

    # Decomposition removes an even detour and retains the odd simple cycle.
    composite = (
        ("a","x",0), ("x","a",0),
        ("a","b",1), ("b","c",1), ("c","a",1),
    )
    simple = _odd_simple_cycle(composite)
    assert simple == composite[2:]
    assert sum(f for _,_,f in simple) % 2 == 1

    # Certificates identify edges by endpoints, so ambiguous multigraph inputs
    # are rejected until the API carries stable edge IDs.
    r = separate_cycle_inequality([("a","a",.5)])
    assert not r.violated and r.reason == "self-loops are not supported"
    r = separate_cycle_inequality([("a","b",.2),("b","a",.8)])
    assert not r.violated and r.reason == "parallel undirected edges are not supported"

    # Boundary is strict: a two-edge backtrack can attain exactly 1, not violate.
    r = separate_cycle_inequality([("a","b",.2)])
    assert not r.violated


if __name__ == "__main__":
    _self_test()
    print("cycle inequality separator self-test: ok")
