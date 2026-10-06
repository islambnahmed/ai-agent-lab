"""Worker A: shared-bias stress test for multi-source feedback.

Extends worker_a_source_diversity.py by separating two failure modes:
1) source-specific persistent bias (rho_ind), which diversity can average out;
2) a shared persistent bias (rho_shared), which flips every source for a bit.

The hypothesis under attack: "more sources => reliable feedback". If sources
share a hidden cause, nominal source count can greatly overstate effective
independence. This script measures that failure directly.
"""
import random

def recover(target, d, p, rho_ind, rho_shared, k, rng, margin=5, cap=21):
    got = 0
    cost = 0
    for i in range(d):
        shared_bad = rng.random() < rho_shared
        bad = [shared_bad or (rng.random() < rho_ind) for _ in range(k)]
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

def experiment(d=12, trials=10000, seed=17, p=0.1, rho_ind=0.02):
    rows = []
    for rho_shared in (0.0, 0.01, 0.02, 0.05, 0.10):
        for k in (1, 3, 5, 7, 11):
            rng = random.Random(seed)
            ok = total_cost = 0
            for _ in range(trials):
                success, cost = recover(
                    rng.randrange(1 << d), d, p, rho_ind, rho_shared, k, rng
                )
                ok += success
                total_cost += cost
            rows.append((rho_shared, k, ok / trials, total_cost / trials))
    return rows

if __name__ == "__main__":
    print("shared_bias, sources, success_rate, mean_cost")
    for row in experiment():
        print(row)
