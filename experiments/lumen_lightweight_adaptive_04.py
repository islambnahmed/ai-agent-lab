"""Lumen: counterexample for naive surprise-triggered adaptive forgetting.

A high learning rate on every prediction error adapts quickly to a real regime
shift, but the same mechanism overreacts to isolated label noise. This experiment
makes that stability/plasticity tradeoff explicit at constant memory size.
"""
from typing import Dict, Tuple

Key = Tuple[str, int]
KEYS: list[Key] = [("A", 0), ("A", 1), ("B", 0), ("B", 1)]
OLD = dict(zip(KEYS, (0, 1, 1, 0)))
SHIFT = {k: 1 - y for k, y in OLD.items()}


class Memory:
    def __init__(self, adaptive: bool, fixed_alpha: float = 0.10,
                 slow_alpha: float = 0.05, fast_alpha: float = 0.60):
        self.adaptive = adaptive
        self.fixed_alpha = fixed_alpha
        self.slow_alpha = slow_alpha
        self.fast_alpha = fast_alpha
        self.state: Dict[Key, float] = {}

    def predict(self, key: Key) -> int:
        return int(self.state.get(key, 0.5) >= 0.5)

    def update(self, key: Key, y: int) -> None:
        old = self.state.get(key, 0.5)
        if self.adaptive:
            alpha = self.fast_alpha if self.predict(key) != y else self.slow_alpha
        else:
            alpha = self.fixed_alpha
        self.state[key] = (1.0 - alpha) * old + alpha * y

    def learn_pass(self, mapping: dict[Key, int]) -> None:
        for key in KEYS:
            self.update(key, mapping[key])

    def accuracy(self, mapping: dict[Key, int]) -> float:
        return sum(self.predict(k) == y for k, y in mapping.items()) / len(KEYS)


def prepared(adaptive: bool) -> Memory:
    m = Memory(adaptive)
    m.learn_pass(OLD)
    m.learn_pass(OLD)
    return m


def shift_recovery(adaptive: bool) -> tuple[float, float, int]:
    m = prepared(adaptive)
    before = m.accuracy(SHIFT)
    m.learn_pass(SHIFT)
    return before, m.accuracy(SHIFT), len(m.state)


def isolated_noise(adaptive: bool) -> tuple[float, int]:
    m = prepared(adaptive)
    # One contradictory observation per key, but the underlying regime did not change.
    for key in KEYS:
        m.update(key, 1 - OLD[key])
    return m.accuracy(OLD), len(m.state)


def main() -> None:
    fixed_shift = shift_recovery(False)
    adaptive_shift = shift_recovery(True)
    fixed_noise = isolated_noise(False)
    adaptive_noise = isolated_noise(True)

    print("agent,shift_before,shift_after_one_pass,stable_accuracy_after_noise,cells")
    print(f"fixed,{fixed_shift[0]:.2f},{fixed_shift[1]:.2f},{fixed_noise[0]:.2f},{fixed_shift[2]}")
    print(f"adaptive,{adaptive_shift[0]:.2f},{adaptive_shift[1]:.2f},{adaptive_noise[0]:.2f},{adaptive_shift[2]}")

    assert fixed_shift == (0.0, 0.0, 4)
    assert adaptive_shift == (0.0, 1.0, 4)
    assert fixed_noise == (1.0, 4)
    assert adaptive_noise == (0.0, 4)


if __name__ == "__main__":
    main()
