# Khepri experiment 409 — nonoverlapping backtests are not necessarily independent

Date: 2026-10-24. Research-only; no change to main.

## Question and source

Does stride >= horizon make forecast-evaluation *errors* independent? The current tools/gold_walkforward.py (main blob 1bf63b9fce9f8d1e237f3e45b48e1bdc978e4e08) ensures nonoverlapping target intervals and calls the resulting count independent_windows. It sets status=evaluation_ready at 20 windows, **but does not assert statistical significance or calculate p-values**. The investigation tests whether downstream inference could safely treat the window count as independent evidence.

## Finding 1 — correlated error differences inflate naive certainty

benchmark.py generates stationary zero-mean Gaussian AR(1) paired error differences, 2,500 fixed-seed replications per condition, with a 100-observation burn-in. These are deliberately controlled synthetic *null* differences, not genuine backtest errors. A naive abs(mean / naive_SE) > 1.96 diagnostic was triggered:

| n | AR(1) phi | naive trigger rate | Bartlett-HAC trigger rate | exact effective n |
|---:|---:|---:|---:|---:|
| 20 | 0.0 | 7.76% | 15.24% | 20.00 |
| 20 | 0.8 | 56.80% | 39.16% | 2.85 |
| 20 | 0.9 | 71.24% | 54.80% | 1.80 |
| 60 | 0.0 | 5.08% | 10.04% | 60.00 |
| 60 | 0.8 | 54.16% | 22.92% | 7.20 |
| 60 | 0.9 | 68.68% | 34.92% | 3.75 |

**Important negative result:** naive Bartlett-HAC with short samples is *not* a calibrated fix; even at phi=0 its trigger rate is too high for a nominal 5% two-sided test. No p-value or significance guarantee is offered by this prototype. Exact finite-sample AR(1) variance inflation is computed separately as 1 + 2 sum((1-k/n) phi^k).

## Finding 2 — actual upstream backtest, two different synthetic data mechanisms

Using the exact upstream backtest code and 60 deterministic seeds per case, with 400 observations each:

| synthetic case | process | windows | mean lag-1 correlation of paired MAE differences | fraction of runs with lag-1 > .2 |
|---|---|---:|---:|---:|
| gold | iid log returns, horizon 7 | 40 | -0.0792 | 6.67% |
| gold | AR(1) log returns phi=.9, horizon 7 | 40 | +0.3590 | 80.00% |
| SEO | iid latent returns + 7-day seasonality, horizon 3 | 93 | +0.0232 | 35.00% |
| SEO | AR(1) latent returns phi=.9 + 7-day seasonality, horizon 3 | 93 | -0.5588 | 0.00% |

All 240 runs were labeled evaluation_ready by upstream. That is a count-based label, **not a bug in a significance test**, because upstream does not implement one. In one SEO run, lag-1 autocorrelation was **-0.6619**, yet lag-7 was **+0.7738**. An AR(1)-only effective-sample-size diagnostic clipped to n would miss this periodic dependence. The multi-lag autocorrelation audit explicitly flags it. This is a counterexample to the shortcut "check only positive lag-1 autocorrelation".

## Prototype

dependence_audit.py accepts paired per-window MAE differences (baseline_abs_error - candidate_abs_error) and reports lag 1–10 autocorrelations, a *conditional* AR(1) effective-sample-size diagnostic, naive/HAC standard-error diagnostics, and a heuristic flag for strong higher-lag structure. It can consume an upstream backtest result without changing it. It **does not** decide model superiority, calculate validated p-values, or recommend trades. test_dependence_audit.py has 16 passing tests. benchmark.py includes a second, seasonal synthetic application (SEO).

## Reproduction

From the repository root:

    PYTHONPATH=experiments/khepri/exp409 python -m unittest discover -s experiments/khepri/exp409 -p 'test_dependence_audit.py' -v
    PYTHONPATH=experiments/khepri/exp409 python experiments/khepri/exp409/benchmark.py

The offline ZIP includes an exact snapshot of upstream tools/gold_walkforward.py (Git blob SHA above) for independent reruns. results.json contains fixed-seed output when provided.

## Limitations and next experiment

The simulations are synthetic and cannot estimate real gold-market failure rates. AR(1) is a deliberately simple null; SEO seasonality violates it. Autocorrelation estimates are noisy at n=20. The HAC estimator uses Bartlett weights and a heuristic lag count, not finite-sample calibration. The strong_higher_lag_structure_heuristic threshold of 0.5 is exploratory, not a validated detector. Next: use an untouched real series (if available within authorized lab) and evaluate block bootstrap, seasonal block resampling, and predeclared model selection with out-of-sample holdout.
