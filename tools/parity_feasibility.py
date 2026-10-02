"""Fast feasibility check for deterministic binary pair constraints.

Constraint (u, v, parity): parity=0 means X_u == X_v; parity=1 means X_u != X_v.
Optional marginals map node -> P(X_node=1).

This is intentionally a fast path, not a solver for general probabilistic edges.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Hashable, Iterable, Mapping

Node = Hashable
Constraint = tuple[Node, Node, int]


@dataclass(frozen=True)
class FeasibilityResult:
    feasible: bool
    reason: str = ""


class ParityDSU:
    def __init__(self) -> None:
        self.parent: dict[Node, Node] = {}
        self.rank: dict[Node, int] = {}
        self.xor_to_parent: dict[Node, int] = {}

    def _add(self, x: Node) -> None:
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0
            self.xor_to_parent[x] = 0

    def find(self, x: Node) -> tuple[Node, int]:
        self._add(x)
        p = self.parent[x]
        if p == x:
            return x, 0
        root, px = self.find(p)
        self.xor_to_parent[x] ^= px
        self.parent[x] = root
        return root, self.xor_to_parent[x]

    def union(self, a: Node, b: Node, parity: int) -> bool:
        if parity not in (0, 1):
            raise ValueError("parity must be 0 (same) or 1 (opposite)")
        ra, xa = self.find(a)
        rb, xb = self.find(b)
        if ra == rb:
            return (xa ^ xb) == parity

        # Need value(ra) XOR value(rb) = xa XOR xb XOR parity.
        link = xa ^ xb ^ parity
        if self.rank[ra] < self.rank[rb]:
            self.parent[ra] = rb
            self.xor_to_parent[ra] = link
        else:
            self.parent[rb] = ra
            self.xor_to_parent[rb] = link
            if self.rank[ra] == self.rank[rb]:
                self.rank[ra] += 1
        return True


def check_feasible(
    constraints: Iterable[Constraint],
    marginals: Mapping[Node, float] | None = None,
    *,
    tol: float = 1e-12,
) -> FeasibilityResult:
    dsu = ParityDSU()
    for u, v, parity in constraints:
        if not dsu.union(u, v, parity):
            return FeasibilityResult(False, f"parity contradiction on edge {u!r}-{v!r}")

    if not marginals:
        return FeasibilityResult(True)

    # Within a connected component, parity fixes whether each marginal equals
    # a common root probability q or its complement 1-q.
    root_q: dict[Node, float] = {}
    for node, p in marginals.items():
        if not (0.0 - tol <= p <= 1.0 + tol):
            return FeasibilityResult(False, f"invalid marginal for {node!r}: {p}")
        root, parity = dsu.find(node)
        q = p if parity == 0 else 1.0 - p
        if root in root_q and abs(root_q[root] - q) > tol:
            return FeasibilityResult(False, f"marginal contradiction in component {root!r}")
        root_q[root] = q

    return FeasibilityResult(True)


def _self_test() -> None:
    # Odd anticorrelation cycle: impossible.
    assert not check_feasible([("a","b",1),("b","c",1),("c","a",1)]).feasible
    # Even anticorrelation cycle: feasible.
    assert check_feasible([("a","b",1),("b","c",1),("c","d",1),("d","a",1)]).feasible
    # Mixed triangle with even XOR parity: feasible.
    assert check_feasible([("a","b",1),("b","c",1),("c","a",0)]).feasible
    # Marginals must respect same/opposite relations.
    assert check_feasible([("a","b",1)], {"a":0.2, "b":0.8}).feasible
    assert not check_feasible([("a","b",1)], {"a":0.2, "b":0.7}).feasible


if __name__ == "__main__":
    _self_test()
    print("parity feasibility self-test: ok")
