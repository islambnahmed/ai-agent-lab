# Khepri exp433 — minimax-regret planning under uncertain risk weights

**2026-10-25 · Offline synthetic benchmark · Python standard library only.**

## Question

Exp431–432 optimized a budgeted, prerequisite-aware test portfolio assuming that risk weights are correct. Does exact optimization of the *wrong* midpoint weights produce brittle decisions? Can minimax regret protect against interval uncertainty, and at what average-case cost?

## Model

Each risk `r` has an independent interval `[lower_r, upper_r]` of possible nonnegative values. A plan covers the union of risks of its selected tasks, subject to integer budget and a prerequisite DAG. Enumerate all feasible task subsets (at most 12 tasks). Three policies:

- **Nominal:** maximize covered value at each interval midpoint.
- **Maximin:** maximize covered value at each interval lower bound.
- **Minimax regret:** minimize the largest difference between the best feasible plan *in hindsight* and the selected plan.

For selected plan `P` and competing plan `Q`, the exact worst-case regret of `P` against `Q` is `sum(upper[r] for r in Q\P) - sum(lower[r] for r in P\Q)` where `P`, `Q` denote *covered risks*, not tasks. Maximizing over all feasible `Q` gives exact worst-case regret for independent Cartesian-product intervals. This identity was checked against brute-force enumeration of interval corners.

The model only *plans* checks. It does not execute tests, access external data, or trade.

## Reproduce

From this directory:

```bash
python -m unittest -v test_robust.py
python benchmark.py > results.json
```

Six unit/property tests passed, including 15 random instances checked against all 256 interval vertices for each feasible plan, 120 random cross-domain dominance checks, dependency validation, and interval validation. Deterministic benchmark: 300 instances each for SEO and gold, 9 synthetic tasks and 8 risks per instance; 12 independent sampled weight vectors per case under each of three distributions (uniform, low-skewed Beta(2,6), high-skewed Beta(6,2)). No empirical SEO or market data.

## Measured outcomes (lower regret is better)

| Domain | Policy | Mean exact worst-case regret | Mean sampled regret, uniform | Mean sampled regret, low | Mean sampled regret, high |
|---|---|---:|---:|---:|---:|
| SEO | Nominal | 12.3767 | **1.0627** | **0.5208** | **0.2949** |
| SEO | Maximin | 16.7800 | 3.7517 | 1.3341 | 4.6897 |
| SEO | Minimax regret | **12.0433** | 1.3402 | 0.6518 | 0.6544 |
| Gold | Nominal | 13.2967 | **1.2019** | **0.6223** | **0.3765** |
| Gold | Maximin | 17.1400 | 3.3356 | 1.1581 | 4.0397 |
| Gold | Minimax regret | **12.9767** | 1.3936 | 0.7797 | 0.6458 |

Minimax regret strictly improved the exact worst-case bound versus nominal in **21/300 SEO** and **20/300 gold** cases; tied otherwise. Nominal beat minimax in observed uniform sampled regret in **20/300 SEO** and **15/300 gold** cases (per-case sample comparison). The robust policy reduces the worst-case bound by design, but often sacrifices expected performance under the assumed uniform data-generating process. Maximin utility is a different objective and need not minimize regret.

## Counterexamples and limits

1. **Risk preference mismatch:** With budget one, A value `[9,10]` and B value `[0,20]`, nominal and minimax choose B while maximin chooses A. Maximin's worst regret is 11; minimax's is 10. "Most conservative" depends on the objective.
2. **Nominal vs minimax:** SEO seed 433017 yields nominal worst regret 12 and minimax 9; gold seed 533023 yields 21 vs 20. Full inputs are in generated `results.json`.
3. **Correlation:** If A and B are actually always equal, although both declared `[0,10]`, choosing either has *zero actual regret*, while the independent-interval model reports worst regret 10. The Cartesian uncertainty set can be overly pessimistic when actual constraints link risks.
4. **Misspecified bounds:** No method protects against actual risk values falling outside their declared intervals. Worst-case guarantees are conditional on coverage, costs, prerequisites, and bounds being correct.
5. **Computational scope:** Exact enumeration is limited to 12 tasks; no claim of scalability or real-world improvement. Synthetic domains differ by labels and random seeds, not by empirically calibrated distributions.

## Transferable lesson

Optimization accuracy and uncertainty robustness are separate axes. Even exact nominal optimization can be vulnerable to uncertain inputs. Minimax regret gives a *provable* interval worst-case guarantee in small instances, but that guarantee is not a free improvement in expected utility. Pick the uncertainty set and objective explicitly, validate bounds, and report both worst-case and distributional performance.
