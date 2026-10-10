# Worker A — low-memory anytime branch-and-bound (2026-10-10)

## Question and approach
The previous bounded knapsack solver refused tasks when the 0/1 dynamic-programming array exceeded a 1,000-cell budget and a cheap 5%-quality certificate failed. Can a depth-first search with a bounded number of expanded nodes improve coverage without a capacity-sized DP array?

Use a **density-ordered DFS branch-and-bound** with a greedy feasible incumbent. The search stack contains at most one unexplored sibling per depth, so its logical size is O(number of items), not O(capacity). Every unvisited subtree has a valid integer-floored fractional-knapsack upper bound. At budget exhaustion, the maximum of the incumbent and the upper bounds of *all* pending subtrees is a global upper bound. Return an answer only if it is exact or satisfies `(UB - candidate)/UB <= 5%`; otherwise return `DEFER`. This is a node budget, **not** a hard RSS/CPU/energy budget.

## Reproducibility and checks
- Reusable core: `experiments/worker_a_memory_bnb.py`, stdlib only, with its own independent exact-DP self-test. This source was committed on this branch. The broader local benchmark harness also used the prior `worker_a_bounded_solver.py` from the previous run; its full local benchmark output is not represented as a committed file.
- 420 small-case checks (6 regimes, 10 seeds, 7 node budgets) against exhaustive subset enumeration and DP, plus 960 30-item quality checks (6 regimes × 40 cases × 4 policies). Zero incorrect accepted certificates or exact results.
- Independent heldout: four seeds (9141–9144), 100 tasks/seed, for each of three 30-item domains (1,200 tasks). Exact DP is used only to **check** results, not to produce certificates.
- Compared DFS budgets of 128 and 512 expanded nodes against the previous `bounded1000` policy (1,000 DP cells maximum, otherwise root certificate or DEFER).
- All positive integer weights/values; no zero or negative weights, no external data, no LLM.
- Memory numbers are Python `tracemalloc` peaks while processing each heldout stream with inputs preloaded, not OS RSS, native allocations, battery power, or strict per-request memory bounds. Traced timing includes instrumentation; do not interpret as optimized speed.

## Heldout results (400 cases per domain)

| Domain | Policy | Exact | <=5% certified (not proven exact) | DEFER | Python traced peak | Instrumented elapsed for 400 |
|---|---|---:|---:|---:|---:|---:|
| large_lumpy | DP-cell-1000 | 0 | 132 | **268** | 4.34 KiB | 0.085 s |
| large_lumpy | DFS-128 | 330 | 38 | **32** | 5.62 KiB | 0.271 s |
| large_lumpy | DFS-512 | 400 | 0 | **0** | 5.52 KiB | 0.292 s |
| large_shift | DP-cell-1000 | 0 | 397 | 3 | 4.34 KiB | 0.105 s |
| large_shift | DFS-128 | 311 | 89 | 0 | 6.11 KiB | 0.358 s |
| large_shift | DFS-512 | 397 | 3 | 0 | 6.11 KiB | 0.391 s |
| large_packing | DP-cell-1000 | 0 | 400 | 0 | 4.31 KiB | 0.048 s |
| large_packing | DFS-128 | 36 | 364 | 0 | 6.53 KiB | 0.319 s |
| large_packing | DFS-512 | 127 | 273 | 0 | 6.62 KiB | 0.726 s |

A simple root-certificate-first, DFS-512-on-failure cascade answered all 400 tasks in each domain: in large_lumpy, 132 root-certified and 268 exact via DFS (0.307 s instrumented); in large_shift, 398 certified and 2 exact (0.105 s); in large_packing, all 400 root-certified (0.047 s). The cascade reduces needless DFS on easy domains but is **not** faster than DFS-only in hard lumpy on this run.

## Interpretation
**Meaningful improvement in coverage, not a free speedup.** On heldout large_lumpy, a bounded DFS-128 improved accepted coverage from 132/400 (33%) to 368/400 (92%) with zero observed quality violations; DFS-512 reached 400/400, at higher CPU time and a modestly higher traced Python allocation peak. The DFS budget and the 1,000-DP-cell budget are **different resources**; equal numerical budgets would not be an apples-to-apples comparison.

A depth-first bounded search can be a useful fallback when the root certificate fails, especially for low-cardinality capacity constraints. On domains where the root certificate already succeeds, running DFS is wasted work. This strengthens the case for a **cheap certificate → bounded search → honest DEFER** cascade. The finite zero-error observations are backed by the upper-bound proof, but only for this mathematical problem.

## Failure conditions and next step
- Repeat on harder correlated, adversarial, and shifted distributions where 512 nodes may be insufficient. Measure the rate of honest deferral, not only accepted quality.
- Account for *actual* peak RSS, latency tail (p95/p99), CPU energy, and object overhead on a target low-memory device; `tracemalloc` is insufficient.
- Avoid claiming any small language model or phone agent was built. Test an actual agent task with independently checkable outputs before generalizing.
