"""Lumen: tiny adaptive-memory benchmark.

A deterministic learn -> transfer -> distribution-shift task with three agents:
stateless, global-memory, and context-memory. Pure Python stdlib.
"""
from dataclasses import dataclass
from typing import Dict, Tuple

Example = Tuple[str, int, int]

TRAIN: list[Example] = [
    ("A", 0, 0), ("A", 1, 1), ("A", 0, 0), ("A", 1, 1),
    ("B", 0, 1), ("B", 1, 0), ("B", 0, 1), ("B", 1, 0),
]
TRANSFER: list[Example] = [
    ("A", 0, 0), ("A", 1, 1), ("B", 0, 1), ("B", 1, 0),
]
SHIFT: list[Example] = [
    ("A", 0, 1), ("A", 1, 0), ("B", 0, 0), ("B", 1, 1),
]


@dataclass
class MajorityMemory:
    contextual: bool
    counts: Dict[Tuple[str, int], list[int]]

    def __init__(self, contextual: bool):
        self.contextual = contextual
        self.counts = {}

    def key(self, context: str, x: int) -> Tuple[str, int]:
        return (context if self.contextual else "*", x)

    def learn(self, examples: list[Example]) -> None:
        for context, x, y in examples:
            bucket = self.counts.setdefault(self.key(context, x), [0, 0])
            bucket[y] += 1

    def predict(self, context: str, x: int) -> int:
        bucket = self.counts.get(self.key(context, x), [0, 0])
        return 1 if bucket[1] > bucket[0] else 0

    @property
    def memory_cells(self) -> int:
        return 2 * len(self.counts)


def accuracy(predict, examples: list[Example]) -> float:
    return sum(predict(c, x) == y for c, x, y in examples) / len(examples)


def run() -> None:
    stateless = lambda _c, _x: 0
    global_mem = MajorityMemory(contextual=False)
    context_mem = MajorityMemory(contextual=True)
    for agent in (global_mem, context_mem):
        agent.learn(TRAIN)

    rows = [
        ("stateless", accuracy(stateless, TRANSFER), accuracy(stateless, SHIFT), 0),
        ("global", accuracy(global_mem.predict, TRANSFER), accuracy(global_mem.predict, SHIFT), global_mem.memory_cells),
        ("context", accuracy(context_mem.predict, TRANSFER), accuracy(context_mem.predict, SHIFT), context_mem.memory_cells),
    ]
    print("agent,transfer_accuracy,shift_accuracy,memory_cells")
    for row in rows:
        print(f"{row[0]},{row[1]:.2f},{row[2]:.2f},{row[3]}")

    assert rows[0][1:] == (0.5, 0.5, 0)
    assert rows[1][1:] == (0.5, 0.5, 4)
    assert rows[2][1:] == (1.0, 0.0, 8)


if __name__ == "__main__":
    run()
