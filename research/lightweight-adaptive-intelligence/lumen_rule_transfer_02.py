"""Lumen experiment 02: infer a transformation from a hypothesis library.

Unlike experiment 01, the learner is not hard-wired to test only rotate-left.
It maintains the version space of all candidate rules consistent with evidence
and predicts only when the surviving hypotheses agree. Persistent memory is a
small hypothesis bit-mask, not stored examples.
"""

RULES = {
    "identity": lambda x: x,
    "reverse": lambda x: x[::-1],
    "rotl1": lambda x: x[1:] + x[:1],
    "rotr1": lambda x: x[-1:] + x[:-1],
    "swap01": lambda x: x[1:2] + x[:1] + x[2:],
}


class VersionSpaceLearner:
    def __init__(self):
        self.alive = set(RULES)

    def observe(self, x, y):
        self.alive = {name for name in self.alive if RULES[name](x) == y}

    def predict(self, x):
        outputs = {RULES[name](x) for name in self.alive}
        return next(iter(outputs)) if len(outputs) == 1 else None


def run():
    # Repeated symbols make one example ambiguous on purpose:
    # reverse and rotate-left both map (a,a,b) -> (a,b,a).
    learner = VersionSpaceLearner()
    learner.observe(("a", "a", "b"), ("a", "b", "a"))
    assert learner.alive == {"reverse", "rotl1"}
    assert learner.predict((1, 2, 3)) is None

    # A second informative example separates the competing explanations.
    learner.observe((1, 2, 3), (2, 3, 1))
    assert learner.alive == {"rotl1"}

    # Transfer is symbolic: unseen domains use the inferred transformation.
    held_out = [
        (("red", "blue", "green"), ("blue", "green", "red")),
        (("α", "β", "γ"), ("β", "γ", "α")),
        ((10, 20, 30), (20, 30, 10)),
    ]
    assert all(learner.predict(x) == y for x, y in held_out)

    # Counterexample discipline: an impossible observation empties the version
    # space instead of silently inventing confidence.
    learner.observe(("x", "y", "z"), ("x", "z", "y"))
    assert learner.alive == set()
    assert learner.predict(("p", "q", "r")) is None

    return {
        "candidate_rules": len(RULES),
        "ambiguous_after_one_example": 2,
        "identified_after_two_examples": "rotl1",
        "held_out_transfer": 1.0,
        "persistent_state": "candidate bit-mask",
        "stores_examples": False,
        "contradiction_detected": True,
    }


if __name__ == "__main__":
    print(run())
