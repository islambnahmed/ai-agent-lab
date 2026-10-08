"""Worker A: independent transfer test of cheap exact certificates to 0/1 knapsack.

Standard library only. No oracle label enters the certificate or audit ranking.
A feasible greedy solution V is certified optimal if V == floor(fractional-knapsack UB).
The fractional upper bound is calculated exactly with integer arithmetic.
Independent 0/1 dynamic programming supplies ground truth only for evaluation.
Metrics distinguish proof coverage, actual optimality, error discovery, and work.
"""
import random
from statistics import mean

N = 30
BUDGET = .10


def instance(rng, domain):
    weights = [rng.randint(1, 20) for _ in range(N)]
    if domain == 'packing':
        values = weights[:]
    elif domain == 'mixed':
        values = [max(1, w + rng.randint(-4, 12)) for w in weights]
    elif domain == 'shift':
        values = [rng.randint(1, 50) for _ in weights]
    else:
        raise ValueError(domain)
    cap = int(sum(weights) * (.35 if domain == 'shift' else .5))
    return list(zip(weights, values)), cap


def greedy(items, cap, rule):
    ids = sorted(range(len(items)), key=(
        (lambda i: (-items[i][1]/items[i][0], -items[i][1], i))
        if rule == 'density' else
        (lambda i: (-items[i][1], -items[i][1]/items[i][0], i))))
    total = 0
    for i in ids:
        w, v = items[i]
        if w <= cap:
            cap -= w
            total += v
    return total


def fractional_upper_bound_floor(items, cap):
    ids = sorted(range(len(items)),
                 key=lambda i: (-items[i][1]/items[i][0], -items[i][1], i))
    total = 0
    for i in ids:
        w, v = items[i]
        if cap == 0:
            break
        if w <= cap:
            total += v
            cap -= w
        else:
            total += (cap * v) // w
            break
    return total


def dp_oracle(items, cap):
    dp = [0] * (cap + 1)
    work = 0
    for w, v in items:
        for c in range(cap, w-1, -1):
            dp[c] = max(dp[c], dp[c-w] + v)
            work += 1
    return dp[cap], work


def sample(n, seed, domain):
    rng = random.Random(seed)
    rows = []
    for _ in range(n):
        items, cap = instance(rng, domain)
        pred = greedy(items, cap, 'density')
        alt = greedy(items, cap, 'value')
        upper = fractional_upper_bound_floor(items, cap)
        opt, work = dp_oracle(items, cap)
        assert pred <= opt <= upper, (domain, pred, opt, upper)
        rows.append(dict(pred=pred, alt=alt, upper=upper, opt=opt, work=work,
                         certified=(pred == upper), bad=(pred < opt),
                         gap=(upper-pred), alt_witness=(alt > pred)))
    return rows


def evaluate(rows, domain, seed):
    n = len(rows)
    bad = {i for i, r in enumerate(rows) if r['bad']}
    safe = {i for i, r in enumerate(rows) if r['certified']}
    pool = sorted(set(range(n)) - safe)
    assert not (bad & safe)
    k = min(int(n * BUDGET), len(pool))
    rng = random.Random(seed)
    choices = {
        'random_uncertified': rng.sample(pool, k),
        'fractional_gap_high': sorted(pool, key=lambda i: (-rows[i]['gap'], i))[:k],
        'fractional_gap_low': sorted(pool, key=lambda i: (rows[i]['gap'], i))[:k],
        'alt_witness_first': sorted(pool, key=lambda i: (not rows[i]['alt_witness'], -rows[i]['gap'], i))[:k],
    }
    print(f'{domain}: n={n}, bad={len(bad)/n:.2%}, optimal={1-len(bad)/n:.2%}, '
          f'certified={len(safe)/n:.2%}, uncertified={len(pool)/n:.2%}, '
          f'alt_witness={sum(r["alt_witness"] for r in rows)/n:.2%}, '
          f'mean_dp_updates={mean(r["work"] for r in rows):.1f}')
    for policy, ids in choices.items():
        found = len(bad.intersection(ids))
        print(f'  {policy:22} audits={len(ids)/n:.2%} '
              f'error_recall={found/len(bad) if bad else 0:.2%} '
              f'precision={found/len(ids) if ids else 0:.2%}')
    return {'bad':len(bad)/n, 'certified':len(safe)/n,
            'alt_witness':sum(r['alt_witness'] for r in rows)/n,
            **{name: len(bad.intersection(ids))/len(bad) if bad else 0
               for name, ids in choices.items()}}


def main():
    for domain in ('packing', 'mixed', 'shift'):
        evaluate(sample(1500, 1001, domain), domain, 333)
    print('HELDOUT: four disjoint seeds, 1000 cases per domain/seed')
    for domain in ('packing', 'mixed', 'shift'):
        runs = [evaluate(sample(1000, 3000+s, domain), domain+f'-seed{s}', 9000+s)
                for s in range(4)]
        print('  summary', domain, ' '.join(
            f'{key}={mean(run[key] for run in runs):.2%}'
            for key in ('bad', 'certified', 'random_uncertified',
                        'fractional_gap_high', 'alt_witness_first')))


if __name__ == '__main__':
    main()
