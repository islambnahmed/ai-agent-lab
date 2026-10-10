"""Worker A: bounded-memory, anytime 0/1 knapsack certificates.
Run: python experiments/worker_a_memory_bnb.py
This is a node-budget experiment, NOT a strict byte/RSS or energy limit.
"""
from functools import cmp_to_key
from random import Random

EPS_BPS = 500


def greedy_bound(items, cap):
    def compare(i, j):
        wi, vi = items[i]
        wj, vj = items[j]
        d = vi * wj - vj * wi
        return (-1 if d > 0 else 1) if d else (i > j) - (i < j)
    order = sorted(range(len(items)), key=cmp_to_key(compare))
    value_order = sorted(range(len(items)), key=lambda i: (-items[i][1], i))

    def greedy(ids):
        rem, val = cap, 0
        for i in ids:
            w, v = items[i]
            if w <= rem:
                rem -= w
                val += v
        return val

    candidate = max(greedy(order), greedy(value_order))
    rem, ub = cap, 0
    for i in order:
        w, v = items[i]
        if w <= rem:
            rem -= w
            ub += v
        else:
            ub += rem * v // w
            break
    return candidate, ub


def bounded_bnb(items, cap, node_budget=512, epsilon_bps=EPS_BPS):
    """Return (value_or_none, status, expanded, max_stack).

    The pending DFS stack partitions all unexamined solutions. The maximum
    fractional upper bound across that stack bounds their optimal value.
    Therefore an accepted near-optimality certificate is sound even when
    search stops before completing the tree.
    """
    if node_budget < 0 or cap < 0 or not 0 <= epsilon_bps <= 10000:
        raise ValueError("invalid budget, capacity or epsilon")
    if any(w <= 0 or v <= 0 for w, v in items):
        raise ValueError("weights and values must be positive")
    def compare(i, j):
        wi, vi = items[i]
        wj, vj = items[j]
        d = vi * wj - vj * wi
        return (-1 if d > 0 else 1) if d else (i > j) - (i < j)
    order = sorted(range(len(items)), key=cmp_to_key(compare))
    ordered = [items[i] for i in order]
    best, _ = greedy_bound(items, cap)

    def upper(idx, rem, val):
        ub = val
        for w, v in ordered[idx:]:
            if w <= rem:
                rem -= w
                ub += v
            else:
                ub += rem * v // w
                break
        return ub

    stack = [(0, cap, 0)]
    expanded, max_stack = 0, 1
    while stack and expanded < node_budget:
        idx, rem, val = stack.pop()
        if upper(idx, rem, val) <= best:
            continue
        if idx == len(ordered) or rem == 0:
            best = max(best, val)
            continue
        expanded += 1
        w, v = ordered[idx]
        stack.append((idx + 1, rem, val))
        if w <= rem:
            stack.append((idx + 1, rem - w, val + v))
        max_stack = max(max_stack, len(stack))
    ub = max(best, max((upper(i, r, v) for i, r, v in stack), default=best))
    if not stack or ub == best:
        return best, "exact", expanded, max_stack
    if (ub - best) * 10000 <= epsilon_bps * ub:
        return best, "certified", expanded, max_stack
    return None, "defer", expanded, max_stack


def exact_dp(items, cap):
    dp = [0] * (cap + 1)
    for w, v in items:
        for c in range(cap, w - 1, -1):
            dp[c] = max(dp[c], dp[c - w] + v)
    return dp[cap]


def self_test():
    rng = Random(84001)
    for n in (5, 10, 15):
        for _ in range(80):
            items = [(rng.randint(1, 50), rng.randint(1, 100))
                     for _ in range(n)]
            cap = rng.randint(5, 150)
            optimum = exact_dp(items, cap)
            for budget in (0, 1, 16, 128, 512):
                val, status, nodes, depth = bounded_bnb(items, cap, budget)
                assert nodes <= budget and depth <= n + 1
                if status == "defer":
                    assert val is None
                else:
                    assert val is not None and val <= optimum
                    assert (optimum - val) * 10000 <= EPS_BPS * optimum
                    if status == "exact":
                        assert val == optimum
    print("PASS: 1200 independent exact-DP comparisons")


if __name__ == "__main__":
    self_test()
