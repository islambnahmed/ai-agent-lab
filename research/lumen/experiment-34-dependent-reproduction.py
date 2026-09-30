"""Reproducible dependent martingale-difference control for Experiment 34.

Uses only Python stdlib.  The process is genuinely dependent because the
predictable magnitude at time t depends on the previous innovation, while the
fresh sign keeps E[X_t | F_{t-1}] = 0.
"""
import math
import random

SEED = 20261001
RUNS = 20_000
HORIZON = 500
LAMBDA = 0.25
THRESHOLD = 20.0


def one_run(rng):
    prev_eps = 1 if rng.random() < 0.5 else -1
    e_value = 1.0
    for t in range(1, HORIZON + 1):
        magnitude = 1.0 if prev_eps == 1 else 0.25
        eps = 1 if rng.random() < 0.5 else -1
        x = magnitude * eps
        e_value *= 1.0 + LAMBDA * x
        if e_value >= THRESHOLD:
            return t
        prev_eps = eps
    return None


def dependence_diagnostic(seed=SEED + 1, steps=1_000_000):
    rng = random.Random(seed)
    prev_eps = 1 if rng.random() < 0.5 else -1
    prev_x = None
    sx = sy = sxx = syy = sxy = 0.0
    n = 0
    for _ in range(steps):
        magnitude = 1.0 if prev_eps == 1 else 0.25
        eps = 1 if rng.random() < 0.5 else -1
        x = magnitude * eps
        if prev_x is not None:
            y = abs(x)
            sx += prev_x; sy += y
            sxx += prev_x * prev_x; syy += y * y; sxy += prev_x * y
            n += 1
        prev_x = x
        prev_eps = eps
    cov = sxy / n - (sx / n) * (sy / n)
    vx = sxx / n - (sx / n) ** 2
    vy = syy / n - (sy / n) ** 2
    return cov / math.sqrt(vx * vy)


def main():
    rng = random.Random(SEED)
    crossings = [one_run(rng) for _ in range(RUNS)]
    hits = [t for t in crossings if t is not None]
    print(f"seed={SEED} runs={RUNS} horizon={HORIZON} lambda={LAMBDA} threshold={THRESHOLD}")
    print(f"crossings={len(hits)} rate={len(hits)/RUNS:.5f}")
    print(f"corr(X[t-1], abs(X[t]))={dependence_diagnostic():.5f}")


if __name__ == "__main__":
    main()
