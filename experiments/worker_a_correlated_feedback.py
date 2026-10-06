"""Worker A: correlated/systematic-noise stress test for pairwise feedback.

Unlike worker_a_pairwise_feedback.py, repeated observations are not assumed
independent. For each bit, with probability rho the comparison channel enters
a persistent inverted state for that bit. Repetition cannot average this
failure away. Otherwise observations retain iid flip probability p.

Purpose: test whether the apparent robustness of repeated weak feedback is
actually an independence artifact.
"""
import random

def recover(target, d, p, rho, rng, margin=5, cap=21):
    got = 0
    cost = 0
    for i in range(d):
        persistent_inversion = rng.random() < rho
        vote = 0
        for _ in range(cap):
            truth = bool((target >> i) & 1)
            if persistent_inversion:
                obs = not truth
            else:
                obs = truth if rng.random() > p else not truth
            vote += 1 if obs else -1
            cost += 1
            if abs(vote) >= margin:
                break
        if vote > 0:
            got |= 1 << i
    return got == target, cost

def experiment(d=12, trials=10000, seed=7, p=0.1):
    rows = []
    for rho in (0.0, 0.01, 0.02, 0.05, 0.10):
        rng = random.Random(seed)
        ok = 0
        costs = []
        for _ in range(trials):
            success, cost = recover(rng.randrange(1 << d), d, p, rho, rng)
            ok += success
            costs.append(cost)
        rows.append((rho, ok / trials, sum(costs) / trials, max(costs)))
    return rows

if __name__ == "__main__":
    print("rho, success_rate, mean_cost, max_cost")
    for row in experiment():
        print(row)
