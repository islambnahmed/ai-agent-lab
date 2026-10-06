"""Worker A: weak pairwise feedback with adaptive stopping.

The environment never returns a numeric score. For each bit it only answers a
binary comparison: is the one-bit probe better than the zero baseline? Each
answer is flipped independently with probability p. The agent sequentially
samples until vote margin reaches 5 (or 21 samples), then commits.

This deliberately weakens the prior graded-feedback assumption.
"""
import random

def recover(target, d, p, rng, margin=5, cap=21):
    got = 0
    cost = 0
    for i in range(d):
        vote = 0
        for _ in range(cap):
            truth = bool((target >> i) & 1)
            obs = truth if rng.random() > p else not truth
            vote += 1 if obs else -1
            cost += 1
            if abs(vote) >= margin:
                break
        if vote > 0:
            got |= 1 << i
    return got == target, cost

def experiment(d=12, trials=2000, seed=1):
    rows=[]
    for p in (0.1,0.2,0.3,0.4):
        rng=random.Random(seed)
        ok=0; costs=[]
        for _ in range(trials):
            success,cost=recover(rng.randrange(1<<d),d,p,rng)
            ok += success; costs.append(cost)
        rows.append((p, ok/trials, sum(costs)/trials, max(costs)))
    return rows

if __name__=="__main__":
    for row in experiment():
        print(row)
