# Khepri exp405 — Adaptive fallback after failure is evidence, not just a retry

## Why this pivot
Experiments 403–404 evaluated fixed upfront tool plans under shared outages and common shocks. This experiment changes the decision architecture: after a read-only tool fails, the agent may **stop or select one different fallback**, and pays for that fallback only when it is called. Does observing failure change which fallback is best? Does a deadline change whether sequential execution is worth it?

## Capability built
`adaptive_planner.py` is a pure-Python standard-library planner. It enumerates a two-regime latent common shock and conditional shared failure-domain outages, then integrates conditional endpoint successes. It computes `P(A succeeds)`, `P(A fails AND B succeeds)`, and `P(B succeeds)` exactly under this assumed model. After A fails, it chooses fallback B maximizing `reward × deadline_probability × P(B succeeds | A failed) − fallback_cost`, or stops. It compares the best first-tool/one-fallback policy against the best one-tool or two-tool *parallel* static plan. The deadline probability is an explicit simplification for whether a late fallback result is still useful. No actual tool invocations, network calls, or user data are involved.

## Concrete counterexample: marginal ranking reverses after observing failure
In a synthetic case, B and A share domain X, while C is in domain Y. B's unconditional success is **79.466%** versus C's **75.800%**. But *after A fails*, B's conditional success is only **8.558%**, while C's remains **75.800%**. The correct fallback after A failure is C, despite its lower unconditional reliability. The cause is shared domain outage evidence, not an improvement in C.

## Seeded benchmark, two materially different synthetic cost/reward regimes
`benchmark.py` uses seed 405, 2,000 generated scenarios for each domain/deadline combination (**8,000 total**), with two tools sharing one domain and a third in another. Gold reward is 10 and SEO reward is 15, with different tool cost ranges. Results are expected *model utility*, not real market performance. `marginal_policy_disagreements` counts disagreement in first choice **or** fallback with a deliberately misspecified planner that ignores information from first-tool failure.

| Synthetic regime | Fallback deadline probability | Adaptive beats best static | Mean adaptive minus static utility | Marginal policy disagreements | Mean marginal-policy regret |
|---|---:|---:|---:|---:|---:|
| Gold | 1.0 | 2,000 / 2,000 | +0.650536 | 1,447 / 2,000 | 0.498575 |
| Gold | 0.3 | 595 / 2,000 | -0.219105 | 1,455 / 2,000 | 0.116396 |
| SEO | 1.0 | 2,000 / 2,000 | +0.970039 | 1,397 / 2,000 | 0.747591 |
| SEO | 0.3 | 584 / 2,000 | -0.330012 | 1,441 / 2,000 | 0.174713 |

When deadline probability is 1 and fallback calls have positive cost, adaptive sequencing naturally dominates the same pair run upfront: it avoids fallback cost when the first tool succeeds. This is **structural**, not a surprising empirical discovery. The more informative counterexample is at deadline 0.3: static parallel wins on average because sequential fallbacks often arrive too late. A single illustrative case at deadline 0.1 has best static utility **8.6030772** versus best adaptive **7.75850972**.

## Verification and limits
- **19/19 unit tests passed**, including same-domain inference, independent-domain control, stopping, deadline reversal, and independent seeded Monte Carlo checks.
- The benchmark independently samples shocks, domain outages, endpoint outcomes and fallback timeliness for the first six optimized policies in each family (20,000 runs each). Largest absolute utility differences from exact calculations: **0.044861** (gold deadline 1), **0.039791** (gold deadline 0.3), **0.026704** (SEO deadline 1), **0.047763** (SEO deadline 0.3). Sampling variation is expected.
- Halving the assumed shock probability changes the optimal adaptive policy in **74, 426, 87, 435** scenarios respectively (same row order as table); mean true-model utility regret is **0.000877, 0.040235, 0.001546, 0.071087**. Even correct mathematical inference cannot fix incorrect outage probabilities.
- This is a two-regime model, with conditional independence of endpoints given shock and domain outages. It does **not** learn outage parameters, model actual wall-clock latency, retries beyond one fallback, noisy failure labels, data correctness, or time-varying conditions. The 0.3 deadline assumption is artificial. Not production-ready.

## Reproduce
From this directory with Python 3.10+ (standard library only):

```bash
python3 -m unittest -v test_adaptive.py
python3 benchmark.py
```

`benchmark.py` regenerates `results.json` deterministically. Keep on a research branch; no `main` changes.

## Reusable lesson
Tool failures carry **information** about shared infrastructure. Select fallbacks using their conditional probability of success *after the observed failure*, not their unconditional uptime. But when deadlines matter, parallel calls can beat adaptive sequential retries despite higher invocation cost. This transfers from gold-data fetching to SEO API retrieval as a method, not as a validated field claim.
