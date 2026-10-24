# Khepri experiment 412 — finite-horizon refresh planning

Date: 2026-10-24. Research only. No network, real crawling, trading, or production changes.

## Question and falsifiable claim

Experiment 411 proved exact *one-day* knapsack optimality but warned that it was not globally optimal over multiple days. Does repeatedly taking the highest immediate expected detection reward maximize expected detection impact over a short horizon?

**No.** A small exact dynamic program beats repeated one-step selection. The advantage is not universal and can reverse when change-rate estimates are wrong.

## Method

An item has integer request cost, detection impact, and a stationary independent Poisson change rate per day. At each decision day, an item not checked accumulates age; a check earns `impact * (1 - exp(-rate * (age+1)))` in expected detected impact and resets age to zero. Unchecked items age by one. A check clears pending changes. The action set is all subsets fitting the daily request budget. The DP searches over remaining days and the age vector. The myopic comparator maximizes the same *single-day* objective each day. No stochastic data source is consulted by the planner.

This yields an exact solution for the **specified finite-horizon expected-impact objective** for small problems (at most 6 items, 7 days), not a general optimal scheduling policy. A 150-instance independent brute-force oracle tests DP optimality for 1–4 items over 1–3 days. An independent 100,000-trial paired-event Monte Carlo tests the analytic expectation of a constructed counterexample.

## Evidence

- **15 unit tests passed**, including 150 seeded independently enumerated action-sequence cases.
- Constructed case: costs `(1,3,2,2)`, impacts `(12,16,16,25)`, rates `(.01,.3,.3,.7)`, budget 4, horizon 4. Repeated myopic picks `(c,d)` every day and yields expected 66.9291. Exact DP checks `(a,b)` on day 3 and yields 69.3682 (+2.4391, +3.64%). The `a` item has low rate; most of the benefit comes from accumulating enough age to check `b` economically.
- Independent 100,000-trial paired Monte Carlo: mean difference +2.4605, approximate 95% normal CI `[2.3731, 2.5480]` (fixed seed 412). This confirms the analytic direction under the same simulated model.
- Across 300 seeded synthetic SEO subsets (3–5 pages, horizon 3–5), exact DP strictly beat myopic in **188**, tied in 112; mean absolute gain 1.1297 expected impact units. Across 300 synthetic feed subsets, it won **167**, tied in 133; mean gain 0.6999. These are constructed distributions, not observed domain performance.
- **Counterexample to robustness:** With systematically misspecified rates, lookahead under the wrong model performs worse than myopic under that same wrong model when evaluated at true rates in **44/300 SEO** and **24/300 feed** cases. The exact optimizer is only as good as its model.

## Interpretation

The preceding one-day optimality guarantee does not transfer to repeated decisions: checking a less immediately attractive item can improve the finite-horizon total by allowing others to accumulate detection probability. However, maximizing expected discoveries within a short fixed horizon can also encourage terminal-horizon artifacts; do not mistake it for long-run optimality or fair coverage.

## Limitations

Stationary known rates, independent Poisson events, all-or-nothing pending-change detection, fixed impacts, fixed budgets, and no cost for late detection. Repeated changes before a check count as one discovery. The solver does not handle provider constraints, time-varying rates, real SEO value, financial freshness requirements, coverage guarantees, or observation-conditioned adaptation. A practical extension should benchmark rolling-horizon planning under rate uncertainty and a latency penalty, rather than merely scaling the exact solver.

## Reproduce (Python 3.10+, standard library)

```sh
python -m unittest -v test_planner.py
python benchmark.py
python verify_mc.py
```

Fixed-seed outputs: `results.json`, `mc_results.json`. No changes to main or production.
