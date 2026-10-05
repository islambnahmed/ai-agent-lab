"""Lumen: adaptation speed versus forgetting rate.

Extends experiment 02 by measuring how many complete post-shift passes are
needed for a fixed-size memory to recover. This exposes a threshold effect that
one-pass success alone hides.
"""
from typing import Dict, Tuple

Example = Tuple[str, int, int]

TRAIN: list[Example] = [
    ("A", 0, 0), ("A", 1, 1), ("A", 0, 0), ("A", 1, 1),
    ("B", 0, 1), ("B", 1, 0), ("B", 0, 1), ("B", 1, 0),
]
SHIFT: list[Example] = [
    ("A", 0, 1), ("A", 1, 0), ("B", 0, 0), ("B", 1, 1),
]


class AdaptiveMemory:
    def __init__(self, alpha: float):
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        self.alpha = alpha
        self.state: Dict[Tuple[str, int], float] = {}

    def update(self, context: str, x: int, y: int) -> None:
        key = (context, x)
        old = self.state.get(key, 0.5)
        self.state[key] = (1.0 - self.alpha) * old + self.alpha * y

    def learn(self, examples: list[Example]) -> None:
        for c, x, y in examples:
            self.update(c, x, y)

    def predict(self, context: str, x: int) -> int:
        return int(self.state.get((context, x), 0.5) >= 0.5)

    def accuracy(self, examples: list[Example]) -> float:
        return sum(self.predict(c, x) == y for c, x, y in examples) / len(examples)


def recovery_passes(alpha: float, max_passes: int = 8) -> tuple[int, int]:
    agent = AdaptiveMemory(alpha)
    agent.learn(TRAIN)
    assert agent.accuracy(SHIFT) == 0.0
    for n in range(1, max_passes + 1):
        agent.learn(SHIFT)
        if agent.accuracy(SHIFT) == 1.0:
            return n, len(agent.state)
    raise AssertionError(f"no recovery for alpha={alpha}")


def main() -> None:
    print("alpha,recovery_passes,memory_cells")
    rows = {}
    for alpha in (0.05, 0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.75, 1.0):
        rows[alpha] = recovery_passes(alpha)
        print(f"{alpha:.2f},{rows[alpha][0]},{rows[alpha][1]}")

    # With two identical pre-shift observations per key, slow forgetting retains
    # enough old evidence to require a second pass; faster forgetting crosses
    # the decision boundary after one observation.
    assert all(rows[a][0] == 2 for a in (0.05, 0.10, 0.20, 0.25, 0.30))
    assert all(rows[a][0] == 1 for a in (0.40, 0.50, 0.75, 1.0))
    assert all(cells == 4 for _, cells in rows.values())


if __name__ == "__main__":
    main()
