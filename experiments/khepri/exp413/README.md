# Khepri experiment 413 — censored refresh feedback

2026-10-24. Synthetic, research-only. No real crawling, trading, API access, or production changes.

## Question

Exp412 showed that refresh planning can fail when change rates are misspecified. A refresh check usually reports only **whether at least one change occurred** since the previous check, not the number of changes. Can an agent infer rates without counting a positive interval as exactly one event?

## Method

Under a stationary Poisson model, for an interval of `t` days, `P(positive) = 1 - exp(-lambda*t)`. Implemented a stable posterior-mode estimate for `lambda` using a Gamma(shape=1.5, rate=1) prior and bisection of the monotone score. This handles mixed positive/negative intervals and yields finite estimates for all-positive data, though it cannot recover information lost through saturation.

A paired synthetic simulation compares `censored` (correct binary likelihood), `naive` (one event per positive interval), and `oracle` (true rates). Each chooses two of five items per day for 90 days using myopic `impact * P(change since last check)`. Each run uses identical pre-generated daily latent event flags across policies; 150 independent runs per scenario. The oracle is **not** a globally optimal scheduling bound.

## Evidence

- 13 unit tests passed locally, including numerical score-optimum checks and deterministic reproduction.
- Rate 0.4/day, 3-day intervals, 100 observations × 250 datasets: censored MAP MAE **0.0411** vs naive **0.1658**.
- Rate 2/day, 4-day intervals: censored MAP MAE **0.4170** vs naive **1.7494**.
- Low rate 0.05/day, 2-day intervals: naive MAE **0.01236** slightly better than MAP **0.01351**. No universal dominance.
- Synthetic SEO: mean rewards **421.00** (censored), **373.95** (naive), **464.53** (oracle); paired censored-minus-naive **+47.05**, approximate 95% CI **[44.55,49.54]**.
- Synthetic feeds: **782.01**, **746.27**, **814.82**; mean difference **+35.75**, CI **[31.95,39.55]**.
- Low-rate/equal-impact counterexample: censored **16.67**, naive **16.70**, oracle **16.98**; censored lost in 32/150 runs and CI included zero.
- **Saturation failure:** with true rate 2/day and 100 binary observations, MAP mean rate was **2.029** at 1-day intervals but **0.932** at 8-day intervals. Very long intervals almost always return positive, making high rates unidentifiable.

## Reproduce

Python 3.10+, standard library only. Run from this directory:

```sh
python -m unittest -v test_censored_refresh.py
python benchmark.py
```

The benchmark regenerates `results.json` with fixed seeds. Reported confidence intervals quantify variability under these synthetic generators, not real-world performance.

## Limits and next experiment

Assumes independent stationary Poisson changes, perfect binary detection, no delayed feedback, and repeated changes counted as one detected change. The Gamma prior and myopic objective affect results. Need test short exploratory checks, time-varying rates, and regret against a stronger scheduler before production consideration. Main is unchanged.
