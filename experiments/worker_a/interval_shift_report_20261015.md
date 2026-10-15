# Worker A — synthetic volatility-shift interval audit (2026-10-15)

## Question
Would a fixed 80% absolute-error calibration band remain trustworthy if forecast-error volatility triples after calibration? Would a **causal** rolling band recover coverage, and at what width cost?

## Method (fully synthetic; no gold price feed)
- Python standard library only; deterministic seeds 10000..10399, 400 replicates of 800 one-step errors each.
- Error process: `e_t = rho*e_(t-1) + sigma_t*sqrt(1-rho^2)*Z_t`, `Z_t ~ N(0,1)`; `rho=0` or `0.6`.
- Stationary control: sigma=1 throughout. Shift: sigma=1 before t=500, sigma=3 from t=500.
- Fixed 80% finite-order absolute-error quantile from first 250 errors; rolling quantile from **80 prior errors only**. No future outcomes can influence a current band.
- Evaluate t=300..499 (pre), 500..579 (first 80 after change), 650..799 (late).
- Code: `experiments/worker_a/interval_shift_experiment.py`. Reproduce: `python3 experiments/worker_a/interval_shift_experiment.py --test` then `python3 experiments/worker_a/interval_shift_experiment.py --reps 400`.

## Results
Numbers are mean empirical coverage across 400 synthetic replications. The interval **half-width** is measured in arbitrary simulated error units, not dollars.

| Scenario | Phase | Fixed coverage | Rolling coverage | Fixed half-width | Rolling half-width |
|---|---|---:|---:|---:|---:|
| Stationary, rho=0 | Pre | 80.28% | 80.18% | 1.292 | 1.296 |
| Stationary, rho=0 | Early | 80.36% | 80.55% | 1.292 | 1.302 |
| Stationary, rho=0 | Late | 80.42% | 80.25% | 1.292 | 1.295 |
| Volatility x3, rho=0 | Pre | 80.28% | 80.18% | 1.292 | 1.296 |
| Volatility x3, rho=0 | Early | 32.93% | 59.46% | 1.292 | 2.599 |
| Volatility x3, rho=0 | Late | 33.53% | 80.25% | 1.292 | 3.884 |
| Stationary, rho=0.6 | Pre | 79.95% | 80.31% | 1.290 | 1.303 |
| Stationary, rho=0.6 | Early | 80.70% | 80.18% | 1.290 | 1.290 |
| Stationary, rho=0.6 | Late | 79.92% | 80.04% | 1.290 | 1.301 |
| Volatility x3, rho=0.6 | Pre | 79.95% | 80.31% | 1.290 | 1.303 |
| Volatility x3, rho=0.6 | Early | 33.51% | 59.18% | 1.290 | 2.571 |
| Volatility x3, rho=0.6 | Late | 33.01% | 80.04% | 1.290 | 3.904 |

## Interpretation
A historically calibrated 80% interval **can severely under-cover after a regime change**, even when the point predictor is unchanged. A rolling band adapts after enough new labels, but it **still under-covers early in the shift** and grows about 3x wider. Rolling calibration is not a free accuracy improvement. Neither method has a distribution-free conditional coverage guarantee under shift/dependence.

This experiment deliberately challenges reliance on a single retrospective interval-coverage number in the gold dashboard. It does **not** prove the gold feed has a regime shift, validate gold prices, improve point forecasts, or establish profitable trading. Results are simulated and should not be used to promote a model.

## Next falsification / acceptance criteria
1. Test horizon h=7/30 with **delayed, only-matured** residuals; naive immediate updating would leak labels.
2. Compare rolling/fixed width and realized coverage on a future **prospectively frozen** dataset, not the already inspected retrospective sample.
3. If showing adaptive intervals in UI, label them experimental, display width changes and post-shift undercoverage risk, and never claim guaranteed 80% coverage.

## Verification and boundaries
Five local unittest cases passed for causality, rank boundary, determinism, and no premature calibration. Local simulation run completed with 400 replications. GitHub upload is a proposed research branch, **not merged into main**, and no production forecasting code was changed.
