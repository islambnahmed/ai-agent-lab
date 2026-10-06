"""Worker A: warning-proxy distribution-shift stress test.

Tests whether the previously successful cheap behavioral warning score survives when
failure signatures change at deployment. The router is frozen: same weights, same
6.65% escalation budget. Fixed seed makes the result reproducible.

This is still synthetic; its purpose is falsification of robustness, not validation.
"""

import random

N = 200_000
P_BIAS = 0.05
SEED = 11
BUDGET = 0.0665


def clip(x):
    return min(1.0, max(0.0, x))


def generate(shifted=False):
    rng = random.Random(SEED)
    rows = []
    for _ in range(N):
        biased = rng.random() < P_BIAS
        if not shifted:
            disagreement = clip(rng.gauss(0.72 if biased else 0.22, 0.18))
            instability = clip(rng.gauss(0.63 if biased else 0.18, 0.20))
            margin = clip(rng.gauss(0.25 if biased else 0.78, 0.18))
        else:
            # New failure mode: common-mode errors look confident and stable.
            disagreement = clip(rng.gauss(0.28 if biased else 0.22, 0.18))
            instability = clip(rng.gauss(0.24 if biased else 0.18, 0.20))
            margin = clip(rng.gauss(0.70 if biased else 0.78, 0.18))
        score = 1.4 * disagreement + 1.1 * instability + 1.2 * (1.0 - margin)
        rows.append((biased, score))
    return rows


def evaluate(rows):
    ranked = sorted(rows, key=lambda x: x[1], reverse=True)
    k = int(round(len(rows) * BUDGET))
    total_bias = sum(b for b, _ in rows)
    caught = sum(b for b, _ in ranked[:k])
    recall = caught / total_bias
    residual = (total_bias - caught) / len(rows)
    random_residual = (total_bias / len(rows)) * (1.0 - BUDGET)
    return recall, residual, random_residual


if __name__ == "__main__":
    print("condition       recall     residual   random_equal_budget")
    for name, shifted in (("in-distribution", False), ("shifted", True)):
        recall, residual, random_residual = evaluate(generate(shifted))
        print(f"{name:15s} {recall:9.4%} {residual:11.4%} {random_residual:19.4%}")
