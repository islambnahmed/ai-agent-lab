"""Worker A: diversity stress test for correlated pairwise feedback.

Tests whether multiple independently biased feedback channels can repair the
persistent-error failure found in worker_a_correlated_feedback.py. Each bit has
k sources; each source is persistently inverted with probability rho. Queries
rotate across sources. Ordinary observations have iid flip probability p.

This is deliberately a best-case independence test: it does NOT assume real
world sources are independent. The point is to measure how much source
diversity could matter before testing shared/correlated source bias.
"""
import random

def recover(target, d, p, rho, k, rng, margin=5, cap=21):
    got = 0
    cost = 0
    for i in range(d):
        bad = [rng.random() < rho for _ in range(k)]
        vote = 0
        for r in range(cap):
            source = r % k
            truth = bool((target >> i) & 1)
            if bad[source]:
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

def experiment(d=12, trials=10000, seed=11, p=0.1):
    rows = []
    for rho in (0.02, 0.05, 0.10, 0.20):
        for k in (1, 3, 5, 7):
            rng = random.Random(seed)
            ok = total_cost = 0
            for _ in range(trials):
                success, cost = recover(rng.randrange(1 << d), d, p, rho, k, rng)
                ok += success
                total_cost += cost
            rows.append((rho, k, ok / trials, total_cost / trials))
    return rows

if __name__ == "__main__":
    print("rho, sources, success_rate, mean_cost")
    for row in experiment():
        print(row)
