"""Lumen experiment 06: one-scalar temporal confirmation."""
KEYS = ("A0", "A1", "B0", "B1")
OLD = dict(zip(KEYS, (0, 1, 1, 0)))
NEW = {k: 1-y for k,y in OLD.items()}

class Memory:
    def __init__(self):
        self.state = OLD.copy()
        self.streak = 0

    def accuracy(self, mapping):
        return sum(self.state[k] == mapping[k] for k in KEYS) / len(KEYS)

    def observe(self, mapping):
        coherent = all(self.state[k] != mapping[k] for k in KEYS)
        if coherent:
            self.streak += 1
            if self.streak >= 2:
                self.state.update(mapping)
                self.streak = 0
        else:
            self.streak = 0

def main():
    shifted = Memory()
    assert shifted.accuracy(NEW) == 0.0
    shifted.observe(NEW)
    assert shifted.accuracy(NEW) == 0.0
    shifted.observe(NEW)
    assert shifted.accuracy(NEW) == 1.0

    transient = Memory()
    transient.observe(NEW)
    assert transient.accuracy(OLD) == 1.0
    transient.observe(OLD)
    assert transient.accuracy(OLD) == 1.0

    assert len(shifted.state) + 1 == 5
    print("persistent_shift_after_two=1.0")
    print("transient_noise_stable=1.0")
    print("memory_cells=5")
    print("adaptation_latency_passes=1")

if __name__ == "__main__":
    main()
