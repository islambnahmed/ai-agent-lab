# Worker A — bounded near-optimality certificates (2026-10-10)

## Research question
Can a resource-limited solver cheaply **prove a useful quality guarantee** without proving exact optimality? Test transfer and deliberately hard distribution shift. This is a 0/1 knapsack experiment, **not** an LLM or mobile-agent result.

## Mathematical guarantee
For a feasible candidate value `V`, let `OPT` be the unknown maximum and `UB` a valid upper bound obtained from the integer floor of the fractional-knapsack relaxation (optionally tightened by branching). Then `V <= OPT <= UB`. Therefore

`(OPT - V) / OPT <= (UB - V) / UB`.

If `(UB - V)/UB <= epsilon`, the returned candidate is **provably within epsilon relative loss of optimal**. No oracle answer or DP label is used to generate this certificate. For uncertified cases the hybrid policy runs exact DP as a fallback.

## Reproduction
- Source: `experiments/worker_a_approx_certificates.py`; run `python experiments/worker_a_approx_certificates.py` with Python standard library.
- Five synthetic domains, 30 items, three fixed seeds (6201–6203), 400 instances/seed/domain: **6,000** 30-item instances total. The fifth `lumpy` domain deliberately has small capacity and a loose fractional bound.
- Two cheap feasible candidates: density-greedy and value-greedy; choose larger value. Bound depths 0/2/4 use at most 1/7/31 LP nodes (except early terminal branches).
- Independent exact 0/1 DP checks all 6,000 instances; independent exhaustive subset enumeration matches DP for **100** 12-item instances. Across 1,200 small-case epsilon/depth checks and all large-case checks, **zero invalid certificates**. This is a finite test in addition to the mathematical guarantee.
- Quality thresholds: exact, 1%, 2%, 5% relative optimality loss. The **5% hybrid** returns a certified candidate if possible, otherwise exact DP; its output is not necessarily exact.
- Runtime comparison is end-to-end Python wall-clock, median of three full passes with randomized policy order per domain. It includes candidate sorting, root bound, and exact fallback where needed; excludes task generation and ground-truth evaluation.

## Results

| Domain | Greedy wrong (not exact) | Root exact certified | Root <=1% certified | Root <=2% certified | Root <=5% certified | Observed 5%-hybrid speedup vs exact DP |
|---|---:|---:|---:|---:|---:|---:|
| packing | 5.50% | 94.50% | 99.42% | 100.00% | 100.00% | 7.64x |
| mixed | 54.25% | 17.83% | 60.92% | 92.17% | 100.00% | 7.60x |
| shift | 52.75% | 9.83% | 43.92% | 75.17% | 99.92% | 5.80x |
| adversarial | 79.25% | 11.75% | 37.00% | 55.25% | 94.33% | 6.09x |
| lumpy | 31.58% | 1.08% | 2.25% | 2.92% | 7.17% | **0.65x (slower)** |

Depth-4 branching, at up to 31 bound calls, improved 5% certificate coverage only from 94.33% to 95.08% in adversarial and from 7.17% to 12.50% in lumpy. Exact-certification coverage was much lower than near-optimal coverage in most domains.

The exact-quality (`epsilon=0`) hybrid was **slower** than direct DP on shift (0.95x) and lumpy (0.63x); near-optimal certification is a distinct quality/cost tradeoff, not a free exact solver.

## Interpretation and limits
1. A cheap **proof of bounded error** can be much more useful than an expensive proof of exactness, if the application explicitly tolerates that error.
2. The same method can fail under distribution shift. In `lumpy`, the relaxation is weak, so 92.83% of tasks need the exact fallback and the extra certificate work makes the hybrid **slower** than direct DP. An intelligent controller must decide **whether to attempt certification at all**.
3. Fractional-knapsack upper bounds are mathematically valid for these positive-integer 0/1 knapsack instances. This guarantee does **not** automatically transfer to arbitrary agent reasoning, untrusted external observations, or LLM answers.
4. Benchmarks are synthetic, Python on one machine, three timing passes, no ARM/mobile/RSS/energy measurement. The 5% hybrid is compared against exact DP while returning potentially approximate answers; do not describe the measured speedup as equal-quality exact computation.
5. Increasing proof depth is not automatically worth its computation. Compare actual additional coverage per added LP node and end-to-end cost, not just depth.

## Next experiment
Build an **online cost-aware route selector** that chooses direct exact computation versus cheap candidate+certificate+fallback from observed certificate hit rate and measured costs. Test abrupt transitions from packing/mixed to lumpy, include regret guarantees, adaptation delay, and controller overhead. Retire the policy if overhead or shift makes it worse than direct DP.
