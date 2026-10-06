"""Worker A: can a warning signal be derived from cheap agent behavior?

Synthetic stress test. Shared-bias cases are NOT directly observable. The router only
sees three cheap behavioral features: source disagreement, decision instability, and
decision margin. We compare score-based escalation with random escalation at equal
budget. Fixed seed makes the experiment reproducible.

This is deliberately a toy model: it tests feasibility, not real-world validity.
"""

import random

N = 200_000
P_BIAS = 0.05
SEED = 7
BUDGETS = (0.02, 0.05, 0.0665, 0.10, 0.15, 0.20)


def clip(x):
    return min(1.0, max(0.0, x))


def generate():
    rng = random.Random(SEED)
    rows = []
    for _ in range(N):
        biased = rng.random() < P_BIAS
        disagreement = clip(rng.gauss(0.72 if biased else 0.22, 0.18))
        instability = clip(rng.gauss(0.63 if biased else 0.18, 0.20))
        margin = clip(rng.gauss(0.25 if biased else 0.78, 0.18))
        score = 1.4 * disagreement + 1.1 * instability + 1.2 * (1.0 - margin)
        rows.append((biased, score))
    return rows


def evaluate(rows, budget):
    ranked = sorted(rows, key=lambda x: x[1], reverse=True)
    k = int(round(len(rows) * budget))
    escalated = ranked[:k]
    total_bias = sum(b for b, _ in rows)
    caught = sum(b for b, _ in escalated)
    recall = caught / total_bias
    residual = (total_bias - caught) / len(rows)
    random_residual = (total_bias / len(rows)) * (1.0 - budget)
    gain = random_residual / residual if residual else float("inf")
    return recall, residual, random_residual, gain


if __name__ == "__main__":
    rows = generate()
    print("budget  bias_recall  residual_error  random_equal_budget  gain")
    for b in BUDGETS:
        recall, residual, random_residual, gain = evaluate(rows, b)
        print(f"{b:6.3f}  {recall:11.4%}  {residual:14.4%}  "
              f"{random_residual:19.4%}  {gain:6.1f}x")
