"""Lumen experiment 07: break the global-coherence assumption.

Experiment 06 used one global streak and only adapted when every key contradicted
memory together. That is cheap, but a partial regime shift is invisible forever.

This experiment compares that global detector with one tiny confirmation bit per
key. The local detector adapts only the persistently changed keys after a second
observation while rejecting a one-pass corruption. Cost: 8 scalar cells total
(4 labels + 4 pending bits), still constant in stream length.
"""
KEYS = ("A0", "A1", "B0", "B1")
OLD = dict(zip(KEYS, (0, 1, 1, 0)))
PARTIAL = OLD | {"A0": 1 - OLD["A0"], "B1": 1 - OLD["B1"]}
NOISE = OLD | {"A1": 1 - OLD["A1"]}


class GlobalConfirm:
    def __init__(self):
        self.state = OLD.copy()
        self.streak = 0

    def observe(self, mapping):
        coherent = all(self.state[k] != mapping[k] for k in KEYS)
        if coherent:
            self.streak += 1
            if self.streak >= 2:
                self.state.update(mapping)
                self.streak = 0
        else:
            self.streak = 0


class LocalConfirm:
    def __init__(self):
        self.state = OLD.copy()
        self.pending = {k: False for k in KEYS}

    def observe(self, mapping):
        for k in KEYS:
            if mapping[k] == self.state[k]:
                self.pending[k] = False
            elif self.pending[k]:
                self.state[k] = mapping[k]
                self.pending[k] = False
            else:
                self.pending[k] = True


def accuracy(agent, mapping):
    return sum(agent.state[k] == mapping[k] for k in KEYS) / len(KEYS)


def main():
    global_agent = GlobalConfirm()
    global_agent.observe(PARTIAL)
    global_agent.observe(PARTIAL)
    assert accuracy(global_agent, PARTIAL) == 0.5

    local_agent = LocalConfirm()
    local_agent.observe(PARTIAL)
    assert accuracy(local_agent, PARTIAL) == 0.5
    local_agent.observe(PARTIAL)
    assert accuracy(local_agent, PARTIAL) == 1.0

    transient = LocalConfirm()
    transient.observe(NOISE)
    transient.observe(OLD)
    assert accuracy(transient, OLD) == 1.0

    print("global_partial_shift_after_two=0.5")
    print("local_partial_shift_after_two=1.0")
    print("local_transient_noise_stable=1.0")
    print("global_cells=5")
    print("local_cells=8")
    print("lesson=partial adaptation needs localized temporal evidence")


if __name__ == "__main__":
    main()
