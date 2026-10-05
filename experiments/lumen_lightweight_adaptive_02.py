"""Lumen: constant-memory online adaptation after distribution shift.

Tests whether exponential forgetting can recover from a reversed mapping while
keeping one scalar state per (context, input) key.
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

    @property
    def memory_cells(self) -> int:
        return len(self.state)


def accuracy(agent: AdaptiveMemory, examples: list[Example]) -> float:
    return sum(agent.predict(c, x) == y for c, x, y in examples) / len(examples)


def run(alpha: float) -> tuple[float, float, int]:
    agent = AdaptiveMemory(alpha)
    agent.learn(TRAIN)
    before = accuracy(agent, SHIFT)
    agent.learn(SHIFT)  # one post-shift observation per key
    after = accuracy(agent, SHIFT)
    return before, after, agent.memory_cells


def main() -> None:
    print("alpha,before_shift_adaptation,after_one_pass,memory_cells")
    rows = {}
    for alpha in (0.25, 0.5, 0.75, 1.0):
        rows[alpha] = run(alpha)
        b, a, m = rows[alpha]
        print(f"{alpha:.2f},{b:.2f},{a:.2f},{m}")

    assert rows[0.75] == (0.0, 1.0, 4)
    assert rows[1.0] == (0.0, 1.0, 4)
    assert all(m == 4 for _, _, m in rows.values())


if __name__ == "__main__":
    main()
