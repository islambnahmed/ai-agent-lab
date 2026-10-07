"""Lumen experiment: tiny rule learner vs stateless/retrieval baselines.

Hypothesis: storing a compact abstract transformation can transfer across
superficially different symbol domains with constant persistent memory.
This is intentionally tiny and falsifiable, not a claim of general intelligence.
"""

from dataclasses import dataclass

TASKS = [
    # same latent rule: rotate a 3-item sequence left by one
    ((1, 2, 3), (2, 3, 1)),
    (("red", "blue", "green"), ("blue", "green", "red")),
    (("cat", "owl", "yak"), ("owl", "yak", "cat")),
]

HELD_OUT = [
    (("α", "β", "γ"), ("β", "γ", "α")),
    ((10, 20, 30), (20, 30, 10)),
]


def rotate_left(xs):
    return xs[1:] + xs[:1]


@dataclass
class CompactRuleLearner:
    # One small hypothesis ID; no example storage.
    rule: str | None = None

    def observe(self, x, y):
        if rotate_left(x) == y:
            self.rule = "rotl1"
        elif self.rule == "rotl1":
            # Feedback contradicts the rule: revise rather than cling.
            self.rule = None

    def predict(self, x):
        return rotate_left(x) if self.rule == "rotl1" else x


class RetrievalBaseline:
    def __init__(self):
        self.examples = {}

    def observe(self, x, y):
        self.examples[x] = y

    def predict(self, x):
        return self.examples.get(x, x)


def accuracy(model, cases):
    return sum(model.predict(x) == y for x, y in cases) / len(cases)


def run():
    learner = CompactRuleLearner()
    retrieval = RetrievalBaseline()

    # Stateless identity baseline scores zero on this benchmark.
    stateless = sum(x == y for x, y in HELD_OUT) / len(HELD_OUT)

    # One experience is enough to identify this deliberately small hypothesis.
    x, y = TASKS[0]
    learner.observe(x, y)
    retrieval.observe(x, y)

    transfer = accuracy(learner, HELD_OUT)
    retrieval_transfer = accuracy(retrieval, HELD_OUT)

    assert stateless == 0.0
    assert retrieval_transfer == 0.0
    assert transfer == 1.0
    assert len(retrieval.examples) == 1
    assert learner.rule == "rotl1"

    # Distribution shift: feedback contradicting the learned rule causes revision.
    learner.observe(("a", "b", "c"), ("a", "b", "c"))
    assert learner.rule is None

    return {
        "stateless_transfer": stateless,
        "retrieval_transfer": retrieval_transfer,
        "compact_rule_transfer": transfer,
        "learner_persistent_items": 1,
        "retrieval_persistent_items": len(retrieval.examples),
        "shift_revision": learner.rule is None,
    }


if __name__ == "__main__":
    print(run())
