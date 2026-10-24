# Khepri experiment 411 — budgeted refresh scheduling

2026-10-24. Research-only experiment, no real crawling, provider calls, trades, or production edits.

## Research question

Under a daily request budget, which SEO pages should an agent refresh to maximize expected impact from detecting changes? Can the policy transfer to a different domain (gold-related feed refresh)? What happens when the estimated change rates are wrong?

## Method

Each item has a unique ID, integer request cost, impact, age since last check (days), and estimated Poisson change rate (per day). Probability of at least one change since last check is -expm1(-rate * age). Expected immediate detection reward is impact times that probability. The DP scheduler solves the exact 0/1 knapsack for this **one-day additive reward**; baselines use greedy reward/cost and oldest-first. This is NOT a globally optimal multi-day policy.

- 17 unit tests passed, including 400 fixed-seed small random instances checked independently by exhaustive enumeration.
- A constructed greedy counterexample: budget 10; one item cost 6 and impact 13, versus two items each cost 5 and impact 10 (all near-certain to have changed). Greedy reward/cost selects the first; DP selects the pair.
- 100 paired seeds x 90 days, with identical exogenous change events per policy, for 24 synthetic SEO pages and 12 synthetic data feeds.

## Synthetic results: mean discovered impact per 90-day run

| Case | DP | Ratio | Oldest | Fair DP (30-day guard) | Distorted DP | DP wins vs ratio |
|---|---:|---:|---:|---:|---:|---:|
| SEO | 2455.07 | 2401.46 | 1623.59 | 2383.81 | 1103.23 | 81/100 |
| Data feeds | 1273.40 | 1265.17 | 1102.55 | 1265.49 | 569.26 | 58/100, 4 ties |

**New counterexample: reward optimization can starve coverage.** Over 90 days, unconstrained DP never checked 8/24 SEO pages and 2/12 data feeds. A simple illustrative coverage guard prioritizing items unchecked for 30+ days, then filling the remaining budget with DP, checked all items in both cases. Its mean discovered impact was 2.9% lower for SEO and 0.6% lower for data feeds. This is a coverage-impact trade-off, not a universal fairness guarantee.

**Falsification:** with deliberately distorted rates (impact >= 12 gets rate * 0.05; other items get rate * 10), DP loses badly to simpler baselines. In the data-feed case, oldest-first finds more *individual* changes than DP (104.34 vs 86.13) despite lower total impact. The objective and model calibration matter.

## Limitations

Synthetic independent daily change events, not observed website or financial-feed rates. The model tracks at least one change between checks, not multiple events. There is no delay penalty for discovering a change late. The 30-day guard is heuristic and cannot guarantee a hard maximum age when budgets or costs make the target infeasible. Real deployment would require rate estimation, robots/access constraints, provider rate limits, uncertainty, retry policies, and coverage/fairness guarantees. No live accuracy or SEO gains are claimed.

## Reproduce

From this directory, Python >=3.10, standard library only:

    python -m unittest -v test_scheduler.py
    python benchmark.py

The fixed-seed output is in results.json. The main branch is unchanged.
