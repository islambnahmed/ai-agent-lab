"""Worker A: robustness of linear recovery under noisy graded feedback.

Noise model: each score observation is independently corrupted with probability p
by +/-1 (clipped to 0..d). We repeat each query an odd number of times and use
the median. This tests whether the previous d+1 result survives imperfect feedback.
"""
import random

def score(candidate: int, target: int, d: int) -> int:
    return d - (candidate ^ target).bit_count()

def noisy_score(candidate, target, d, p, rng):
    s = score(candidate, target, d)
    if rng.random() < p:
        s = max(0, min(d, s + rng.choice((-1, 1))))
    return s

def observed(candidate, target, d, p, repeats, rng):
    vals = sorted(noisy_score(candidate, target, d, p, rng) for _ in range(repeats))
    return vals[repeats // 2]

def recover(target, d, p, repeats, rng):
    baseline = observed(0, target, d, p, repeats, rng)
    got = 0
    for i in range(d):
        if observed(1 << i, target, d, p, repeats, rng) > baseline:
            got |= 1 << i
    return got == target

def experiment(d=12, trials=2000, seed=1):
    rows = []
    for p in (0.1, 0.2, 0.3):
        for repeats in (1, 3, 5, 7, 9):
            rng = random.Random(seed)
            successes = sum(recover(rng.randrange(1 << d), d, p, repeats, rng)
                            for _ in range(trials))
            rows.append((p, repeats, successes / trials, (d + 1) * repeats))
    return rows

if __name__ == "__main__":
    for row in experiment():
        print(row)
