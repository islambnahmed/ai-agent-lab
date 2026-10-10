"""Worker A: heldout distribution/size shift stress for bounded knapsack BnB.
Run from experiments/: python worker_a_bnb_shift_stress.py
No dependencies beyond Python stdlib. Uses original worker_a_memory_bnb solver.
"""
from random import Random
from time import perf_counter_ns
from worker_a_memory_bnb import bounded_bnb, exact_dp, greedy_bound


def instance(rng, domain, n):
    if domain == "lumpy":
        items = [(rng.randint(25, 70), rng.randint(20, 120)) for _ in range(n)]
        capacity = 75
    elif domain == "tight_capacity":
        items = [(rng.randint(25, 60), rng.randint(40, 120)) for _ in range(n)]
        capacity = rng.randint(65, 100)
    elif domain == "two_scale":
        items = [
            (rng.randint(1, 3), rng.randint(1, 5))
            if rng.random() < 0.5 else
            (rng.randint(30, 90), rng.randint(30, 150))
            for _ in range(n)
        ]
        capacity = int(sum(w for w, _ in items) * 0.2)
    else:
        raise ValueError(domain)
    return items, capacity


def run():
    print("domain n root_cert bnb128_ok bnb512_ok bnb512_exact p95_ms samples")
    checked = 0
    for domain in ("lumpy", "tight_capacity", "two_scale"):
        for n in (30, 60, 120):
            root = ok128 = ok512 = exact512 = 0
            elapsed = []
            for seed in (88031, 88032, 88033, 88034):
                rng = Random(seed)
                for _ in range(100):
                    items, cap = instance(rng, domain, n)
                    truth = exact_dp(items, cap)  # Independent truth; never a certificate input.
                    candidate, ub = greedy_bound(items, cap)
                    root += (ub - candidate) * 10000 <= 500 * ub
                    a, status_a, expanded_a, stack_a = bounded_bnb(items, cap, 128)
                    start = perf_counter_ns()
                    b, status_b, expanded_b, stack_b = bounded_bnb(items, cap, 512)
                    elapsed.append((perf_counter_ns() - start) / 1e6)
                    ok128 += status_a != "defer"
                    ok512 += status_b != "defer"
                    exact512 += status_b == "exact"
                    assert expanded_a <= 128 and expanded_b <= 512
                    assert stack_a <= n + 1 and stack_b <= n + 1
                    for val, status in ((a, status_a), (b, status_b)):
                        if status == "defer":
                            assert val is None
                        else:
                            assert val <= truth
                            assert (truth - val) * 10000 <= 500 * truth
                            if status == "exact":
                                assert val == truth
                    checked += 2
            p95 = sorted(elapsed)[int(0.95 * (len(elapsed) - 1))]
            print(domain, n, root, ok128, ok512, exact512,
                  f"{p95:.4f}", 400)
    print(f"PASS {checked} independently checked decisions")


if __name__ == "__main__":
    run()
