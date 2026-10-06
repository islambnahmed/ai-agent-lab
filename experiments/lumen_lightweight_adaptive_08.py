"""Lumen experiment 08: test local confirmation under intermittent evidence.

Experiment 07 assumes changed keys are observed contradicting memory on two
consecutive passes. Real streams can revisit the old label between contradictory
observations. A one-bit pending flag then forgets useful evidence immediately.

Compare:
- consecutive confirmation: reset suspicion on any old-label observation;
- leaky evidence: bounded signed score per key, +1 contradiction, -1 agreement,
  adapt at score >= 2.

The leaky detector still has constant memory: one label + one tiny score per key.
"""
KEYS = ("A0", "A1", "B0", "B1")
OLD = dict(zip(KEYS, (0, 1, 1, 0)))
CHANGED_KEY = "A0"


class ConsecutiveConfirm:
    def __init__(self):
        self.state = OLD.copy()
        self.pending = {k: False for k in KEYS}

    def observe_one(self, key, label):
        if label == self.state[key]:
            self.pending[key] = False
        elif self.pending[key]:
            self.state[key] = label
            self.pending[key] = False
        else:
            self.pending[key] = True


class LeakyEvidence:
    def __init__(self, threshold=2):
        self.state = OLD.copy()
        self.score = {k: 0 for k in KEYS}
        self.threshold = threshold

    def observe_one(self, key, label):
        if label == self.state[key]:
            self.score[key] = max(0, self.score[key] - 1)
        else:
            self.score[key] += 1
            if self.score[key] >= self.threshold:
                self.state[key] = label
                self.score[key] = 0


def main():
    old = OLD[CHANGED_KEY]
    new = 1 - old

    # Intermittent evidence: two contradictions separated by one old-label sample.
    stream = (new, old, new)

    consecutive = ConsecutiveConfirm()
    leaky = LeakyEvidence()
    for label in stream:
        consecutive.observe_one(CHANGED_KEY, label)
        leaky.observe_one(CHANGED_KEY, label)

    # With symmetric +1/-1 and threshold 2, neither can adapt yet.
    assert consecutive.state[CHANGED_KEY] == old
    assert leaky.state[CHANGED_KEY] == old

    # One more contradiction is enough for leaky evidence, but consecutive still
    # needs it only because the last sample was already contradictory.
    leaky.observe_one(CHANGED_KEY, new)
    consecutive.observe_one(CHANGED_KEY, new)
    assert leaky.state[CHANGED_KEY] == new
    assert consecutive.state[CHANGED_KEY] == new

    # Harder alternating stream exposes the information tradeoff: if every
    # contradiction is followed by agreement, neither bounded symmetric detector
    # can infer persistence without a prior/noise model.
    alt = (new, old) * 8
    a = ConsecutiveConfirm()
    b = LeakyEvidence()
    for label in alt:
        a.observe_one(CHANGED_KEY, label)
        b.observe_one(CHANGED_KEY, label)
    assert a.state[CHANGED_KEY] == old
    assert b.state[CHANGED_KEY] == old

    print("intermittent_then_confirmed=both_adapt")
    print("alternating_ambiguous=both_stay_old")
    print("cells_per_key=2")
    print("lesson=local evidence helps, but ambiguity remains without assumptions")


if __name__ == "__main__":
    main()
