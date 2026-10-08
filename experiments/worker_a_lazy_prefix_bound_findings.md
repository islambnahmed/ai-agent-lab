# Worker A — lazy prefix-bound verification (2026-10-08)

## Question and hypothesis
Can a **single** 0/1-knapsack proof method avoid expensive repeated O(n) fractional-bound scans without a separate feature router? Pre-run hypothesis: prefix sums plus binary search preserve the exact admissible upper bound and search order, help larger instances, but preprocessing can hurt trivially certifiable instances.

## Method
Existing baseline: density-sorted greedy candidate; bounded depth-first branch-and-bound, suffix-weight-GCD capacity rounding, adjacent-identical-item symmetry, exact integer fractional upper bound. Status is `certified`, `witness`, or `unknown`. No oracle label is used during search.

New method: precompute prefix weights W and values V. At state (i,r), round r down by suffix GCD; let k = bisect_right(W, W[i]+r)-1. Exact same upper bound:
`UB = current_value + V[k]-V[i] + (r-(W[k]-W[i]))*value[k]//weight[k]` if k<n (omit last term otherwise). Search branching is unchanged. `lazy` version evaluates the root with the original linear scan and builds prefix arrays **only if the root cannot certify**. This is an internal proof fast path, not a feature router.

## Verified results
Python stdlib, one local CPU process. Five synthetic domains: packing, mixed, shift, even_shift, duplicates. Four fixed seeds (81051–81054). At 128-node budget: 400 cases/domain for each n=30,100,300 (6,000 total). At 1,024-node budget: 200 cases/domain for n=100,300 (2,000 total). Compared linear, eager-prefix, and lazy-prefix outputs on all 8,000 tasks: **identical status, node count and witness**. Independently brute-forced 200 12-item cases across domains and checked against exact DP; both proof variants were sound on those cases.

Illustrative mean microseconds/case, **including preprocessing**:
| n | domain | budget | linear | eager prefix | lazy prefix |
|---:|---|---:|---:|---:|---:|
| 30 | packing | 128 | 5.19 | 6.47 | 4.38 |
| 100 | packing | 128 | 7.09 | 13.69 | 7.69 |
| 100 | shift | 128 | 132.41 | 64.63 | 64.95 |
| 300 | packing | 128 | 25.37 | 38.00 | 20.31 |
| 300 | mixed | 128 | 176.65 | 48.99 | 41.09 |
| 300 | shift | 128 | 749.56 | 100.42 | 106.21 |
| 300 | duplicates | 128 | 1099.93 | 110.08 | 121.41 |
| 300 | duplicates | 1024 | 2064.36 | 368.12 | 369.71 |

At n=300 duplicates and 128 nodes, eager prefix is ~10.0x faster, lazy ~9.1x, with no change in the fraction unresolved (87%). At n=300 duplicates and 1,024 nodes, lazy is ~5.6x faster but 43.5% remain unresolved. At n=100 packing, lazy is ~8% slower than baseline; **not a universal win**.

## Interpretation and limits
This is a **computational optimization**, not improved proof coverage or an LLM breakthrough. Same decisions and search nodes are produced. Synthetic distributions, one machine/interpreter, no repeated-process confidence intervals, and the lazy variant was always measured third (order effect possible). Runtime excludes instance generation, density sorting, greedy proposal, and oracle; includes bound preprocessing. No mobile power/latency claim.

## Next experiment
Reproduce under randomized three-way timing order and separate processes, then assess whether a similar prefix-indexed bound helps another combinatorial task. Do not endlessly optimize the same knapsack benchmark. Original scripts/logs were created locally as `worker_a_prefix_bound.py`, `worker_a_prefix_bound_results_v2.txt`, and `worker_a_prefix_bound_budget1024.txt`; this report alone does not imply those scripts were uploaded.
