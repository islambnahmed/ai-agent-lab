# Worker A: delayed-label interval stress test (2026-10-15)

Synthetic experiment only; no observed gold prices or claims of trading performance.

The test extends the earlier one-step study to forecast horizons of 7 and 30 index steps. It uses 100 deterministic replications per setting, with 720 issuance indices, correlation parameters 0 and 0.6, and stationary versus threefold volatility-shift scenarios.

A residual from issuance index i is eligible for calibration at index t only if i+h<t. Fixed calibration uses the first 200 residuals. Causal rolling calibration uses the most recent 80 eligible residuals. An intentionally noncausal comparator uses the most recent 80 residuals without waiting for their outcomes; it is included only to quantify evaluation bias.

Results after the volatility shift (early window, rho=0):
- h=7: fixed 32.0% coverage; causal rolling 55.9%; noncausal comparator 60.1%.
- h=30: fixed 31.4%; causal rolling 49.6%; noncausal comparator 64.5%.

Later window (rho=0):
- h=7: fixed 32.7%; causal rolling 79.2%.
- h=30: fixed 33.4%; causal rolling 76.9%.

The longer horizon adapts more slowly because outcome labels become available later. The noncausal comparator appears more accurate early because it uses information unavailable at issuance; it is not suitable for deployment. Neither adaptive method has guaranteed conditional coverage under volatility shifts or dependence.

Reproduce: python3 experiments/worker_a/delayed_horizon_intervals.py --test (seven tests passed locally), then python3 experiments/worker_a/delayed_horizon_intervals.py --reps 100. Source: experiments/worker_a/delayed_horizon_intervals.py on this branch.

Research branch only; main and production forecasting unchanged. Before live use, specify target close times, ensure labels have matured, and validate prospectively.
