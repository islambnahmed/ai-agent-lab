"""Lumen: identifiability limit for shift detection.

A single contradictory pass is observationally identical whether it came from a
persistent regime shift or a transient coherent corruption. Therefore no
detector that sees only that pass can guarantee the correct response. The
experiment then adds one later pass: temporal recurrence supplies the missing
information and makes the two worlds distinguishable.
"""
from typing import Tuple

Key = Tuple[str, int]
KEYS: list[Key] = [("A", 0), ("A", 1), ("B", 0), ("B", 1)]
OLD = dict(zip(KEYS, (0, 1, 1, 0)))
FLIPPED = {k: 1 - y for k, y in OLD.items()}


def observations(mapping: dict[Key, int]) -> tuple[tuple[Key, int], ...]:
    return tuple((k, mapping[k]) for k in KEYS)


def classify_two_passes(first, second) -> str:
    """Minimal recurrence rule; intentionally no hidden oracle state."""
    if first == observations(FLIPPED) and second == observations(FLIPPED):
        return "persistent_shift"
    if first == observations(FLIPPED) and second == observations(OLD):
        return "transient_corruption"
    return "other"


def main() -> None:
    # World S: the rule really changed and remains changed.
    shift_t1 = observations(FLIPPED)
    shift_t2 = observations(FLIPPED)

    # World N: one coherent corrupted pass, then the unchanged rule returns.
    noise_t1 = observations(FLIPPED)
    noise_t2 = observations(OLD)

    # At t1 the learner receives exactly the same evidence in both worlds.
    assert shift_t1 == noise_t1

    # Consequently every deterministic detector f(observation_t1) must emit the
    # same answer in both worlds. A guarantee of different actions is impossible
    # without an additional assumption or additional information.
    detector = lambda obs: hash(obs) % 2
    assert detector(shift_t1) == detector(noise_t1)

    # One later observation breaks the equivalence through recurrence.
    assert classify_two_passes(shift_t1, shift_t2) == "persistent_shift"
    assert classify_two_passes(noise_t1, noise_t2) == "transient_corruption"

    print("first_pass_identical=True")
    print("one_pass_guaranteed_discrimination=False")
    print("two_pass_recurrence_discriminates=True")
    print("extra_memory_requirement=one_previous_pass_signature")


if __name__ == "__main__":
    main()
