"""Worker A: bounded near-optimality certificates for tiny knapsack agents.

Research question: can a small solver certify useful approximate quality even
when exact optimality is hard to prove under domain shift?

No exact labels are used to build candidates, bounds, or certificates. Ground
truth DP and exhaustive enumeration are used ONLY for independent evaluation.
Standard library only. Run: python experiments/worker_a_approx_certificates.py
"""
from functools import cmp_to_key
from statistics import mean, median
from time import perf_counter_ns
import random

DOMAINS = ("packing", "mixed", "shift", "adversarial", "lumpy")
DEPTHS = (0, 2, 4)
EPS_BPS = (0, 100, 200, 500)  # exact, <=1%, <=2%, <=5% relative regret
N = 30
SEEDS = (6201, 6202, 6203)
SAMPLES_PER_SEED = 400


def instance(rng, domain, n=N):
    if domain == "lumpy":
        weights = [rng.randint(25, 70) for _ in range(n)]
        values = [rng.randint(20, 120) for _ in range(n)]
        return list(zip(weights, values)), 75
    if domain == "adversarial":
        weights = [rng.randint(12, 24) for _ in range(n)]
        values = [w + rng.randint(-2, 3) for w in weights]
    else:
        weights = [rng.randint(1, 20) for _ in range(n)]
        if domain == "packing":
            values = weights[:]
        elif domain == "mixed":
            values = [max(1, w + rng.randint(-4, 12)) for w in weights]
        elif domain == "shift":
            values = [rng.randint(1, 50) for _ in weights]
        else:
            raise ValueError(domain)
    fraction = 0.35 if domain in ("shift", "adversarial") else 0.50
    cap = int(sum(weights) * fraction)
    return list(zip(weights, values)), cap


def density_order(items):
    def compare(i, j):
        wi, vi = items[i]
        wj, vj = items[j]
        diff = vi * wj - vj * wi
        if diff:
            return -1 if diff > 0 else 1
        if vi != vj:
            return -1 if vi > vj else 1
        return (i > j) - (i < j)
    return sorted(range(len(items)), key=cmp_to_key(compare))


def greedy(items, cap, order):
    score = 0
    for i in order:
        w, v = items[i]
        if w <= cap:
            cap -= w
            score += v
    return score


def candidate_value(items, cap, ids):
    value_ids = sorted(range(len(items)), key=lambda i: (-items[i][1], i))
    return max(greedy(items, cap, ids), greedy(items, cap, value_ids))


def lp_upper(items, cap, ids, inside, outside):
    """Integer floor of a valid fractional relaxation for a fixed branch."""
    value = 0
    for i in inside:
        w, v = items[i]
        cap -= w
        value += v
    if cap < 0:
        return -1, None
    for i in ids:
        if i in inside or i in outside:
            continue
        w, v = items[i]
        if w <= cap:
            cap -= w
            value += v
        else:
            value += (cap * v) // w
            return value, i
    return value, None


def tree_upper(items, cap, ids, depth):
    """Exact admissible upper bound after depth-limited disjoint branching.

    Every feasible 0/1 solution belongs to one branch; each leaf LP upper
    bounds that branch. Max of leaf bounds upper bounds the global optimum.
    """
    calls = 0

    def walk(inside, outside, remaining):
        nonlocal calls
        ub, fractional = lp_upper(items, cap, ids, inside, outside)
        calls += 1
        if ub < 0 or remaining == 0 or fractional is None:
            return ub
        return max(
            walk(inside | {fractional}, outside, remaining - 1),
            walk(inside, outside | {fractional}, remaining - 1),
        )

    return walk(frozenset(), frozenset(), depth), calls


def exact_dp(items, cap):
    dp = [0] * (cap + 1)
    for w, v in items:
        for c in range(cap, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[cap]


def brute(items, cap):
    best = 0
    for mask in range(1 << len(items)):
        weight = value = 0
        for i, (w, v) in enumerate(items):
            if mask >> i & 1:
                weight += w
                value += v
        if weight <= cap:
            best = max(best, value)
    return best


def certified(candidate, ub, epsilon_bps):
    assert 0 <= candidate <= ub
    # 1 - candidate/OPT <= 1 - candidate/UB, since OPT <= UB.
    return (ub - candidate) * 10000 <= epsilon_bps * ub


def exhaustive_checks():
    rng = random.Random(99181)
    checked = 0
    for domain in DOMAINS:
        for _ in range(20):
            items, cap = instance(rng, domain, n=12)
            ids = density_order(items)
            candidate = candidate_value(items, cap, ids)
            truth = brute(items, cap)
            assert truth == exact_dp(items, cap)
            prev = None
            for depth in DEPTHS:
                ub, calls = tree_upper(items, cap, ids, depth)
                assert calls <= (1 << (depth + 1)) - 1
                assert candidate <= truth <= ub, (domain, depth, candidate, truth, ub)
                assert prev is None or ub <= prev
                prev = ub
                for eps in EPS_BPS:
                    if certified(candidate, ub, eps):
                        assert (truth - candidate) * 10000 <= eps * truth
                    checked += 1
    return checked


def evaluate_domain(domain):
    records = []
    for seed in SEEDS:
        rng = random.Random(seed)
        for _ in range(SAMPLES_PER_SEED):
            items, cap = instance(rng, domain)
            start = perf_counter_ns()
            ids = density_order(items)
            candidate = candidate_value(items, cap, ids)
            candidate_ns = perf_counter_ns() - start
            start = perf_counter_ns()
            truth = exact_dp(items, cap)
            exact_ns = perf_counter_ns() - start
            row = {"candidate": candidate, "truth": truth, "bounds": {},
                   "candidate_ns": candidate_ns, "exact_ns": exact_ns,
                   "items": items, "cap": cap}
            prev = None
            for depth in DEPTHS:
                start = perf_counter_ns()
                ub, calls = tree_upper(items, cap, ids, depth)
                elapsed = perf_counter_ns() - start
                assert candidate <= truth <= ub, (domain, seed, depth)
                assert prev is None or ub <= prev
                prev = ub
                row["bounds"][depth] = (ub, calls, elapsed)
                for eps in EPS_BPS:
                    if certified(candidate, ub, eps):
                        assert (truth - candidate) * 10000 <= eps * truth
            records.append(row)
    print(f"{domain:12} n={len(records)} candidate_wrong={mean(r['candidate'] < r['truth'] for r in records):.2%} "
          f"mean_actual_regret={mean((r['truth']-r['candidate'])/r['truth'] for r in records):.3%}")
    root_cost = mean(r['candidate_ns'] + r['bounds'][0][2] for r in records)
    exact_cost = mean(r['exact_ns'] for r in records)
    print(f"  mean candidate+root={root_cost/1e6:.4f}ms exact_DP={exact_cost/1e6:.4f}ms")
    for eps in (0, 500):
        cost = mean(r['candidate_ns'] + r['bounds'][0][2] +
                    (0 if certified(r['candidate'], r['bounds'][0][0], eps)
                     else r['exact_ns']) for r in records)
        print(f"  root-certificate + exact fallback eps={eps/100:.0f}% "
              f"estimated_mean={cost/1e6:.4f}ms speedup_vs_exact={exact_cost/cost:.2f}x")
    for depth in DEPTHS:
        calls = mean(r['bounds'][depth][1] for r in records)
        ms = mean(r['bounds'][depth][2] for r in records) / 1e6
        cover = [mean(certified(r['candidate'], r['bounds'][depth][0], eps) for r in records)
                 for eps in EPS_BPS]
        print(f"  depth={depth} calls={calls:6.2f} ms={ms:7.4f} "
              + " ".join(f"eps{eps/100:.0f}%={pct:.2%}" for eps, pct in zip(EPS_BPS, cover)))
    benchmark_pipelines(domain, records)
    return records


def benchmark_pipelines(domain, records):
    """Direct end-to-end timing, random policy order; no oracle labels used by hybrid."""
    rng = random.Random(70491)
    samples = {mode: [] for mode in ("exact", "hybrid0", "hybrid5")}
    for _ in range(3):
        modes = list(samples)
        rng.shuffle(modes)
        for mode in modes:
            start = perf_counter_ns()
            checksum = 0
            for row in records:
                items, cap = row['items'], row['cap']
                if mode == "exact":
                    result = exact_dp(items, cap)
                else:
                    ids = density_order(items)
                    result = candidate_value(items, cap, ids)
                    ub, _ = tree_upper(items, cap, ids, 0)
                    eps = 0 if mode == "hybrid0" else 500
                    if not certified(result, ub, eps):
                        result = exact_dp(items, cap)
                checksum += result
            elapsed = perf_counter_ns() - start
            samples[mode].append(elapsed / len(records) / 1e6)
            assert checksum > 0
    ref = median(samples['exact'])
    print("  observed end-to-end median ms/case (3 shuffled passes): " +
          " ".join(f"{mode}={median(v):.4f} ({ref/median(v):.2f}x)"
                   for mode, v in samples.items()))


def main():
    checks = exhaustive_checks()
    print(f"PASS {checks} brute-force / DP / certificate comparisons on 100 12-item cases")
    print("depth-specific calls/timings include bound computation only; pipeline estimates use per-case component times")
    for domain in DOMAINS:
        evaluate_domain(domain)
    print("PASS: no invalid certificates across evaluated cases")


if __name__ == "__main__":
    main()
