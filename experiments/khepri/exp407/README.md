# Khepri experiment 407 — geometric-drift numerical stability

2026-10-24. Research branch only; **no production or main changes**.

## Question and source

Can the repo's `tools/gold_walkforward.py` produce non-finite forecasts or crash on mathematically valid, positive, finite input prices? The original `predict_drift` forms each adjacent ratio `b/a` and separately evaluates `exp(horizon * mean(log_returns))` before multiplying by the last price. Upstream source blob at audit time: `1bf63b9fce9f8d1e237f3e45b48e1bdc978e4e08` (main).

## Reproduced counterexamples

1. `[1e-300, 1e300, 1e-300]`, horizon 7: the original raises `ValueError` because an intermediate ratio underflows to zero; mathematically the drift is zero and the positive finite forecast is `1e-300`.
2. `[1e-300, 1e-100]`, horizon 2: original `exp` overflows, although the final forecast is finite (`1e300`).
3. `[1e300, 1e100]`, horizon 2: original multiplier underflows to zero, although the final forecast is positive (`1e-300`).
4. RMSE calculation squares large residuals before taking the square root, so `sqrt((1e300)**2)` raises `OverflowError` even though RMSE is finite. `stable_rmse` uses max-normalization.

Geometric drift uses **endpoints only**: sum of consecutive log returns telescopes to `log(last/first)`. The proposed `predict_drift_stable` uses `log1p` for near-equal endpoints, differences of logs otherwise, and exponentiates the final log price. Mathematically out-of-range forecasts raise `ForecastRangeError`, rather than returning 0 or infinity.

## Evidence (seed 407)

- **11/11 local unit tests passed** against the copied upstream algorithm and the proposed candidate. GitHub CI has not been run.
- 10,000 synthetic extreme-range price paths; 6,921 had a positive finite 80-digit Decimal oracle result. The original raised or returned invalid on **6,111 of those 6,921** representable cases; stable candidate on **0**. Original had 39 additional cases with relative error above 1e-9; stable had 0. Stable max relative error among representable cases: **5.48e-13**.
- 3,079 mathematically unrepresentable cases: candidate raised explicit range error on all 3,079.
- Ordinary-range synthetic gold: 303 paired predictions, max relative difference **1.78e-15**. Synthetic SEO traffic: another 303 paired predictions, max difference **1.78e-15**.
- Synthetic data are intentionally adversarial, not empirical gold/SEO data. Counts do not estimate production failure rates.

## Reproduction

From the repository root on this branch:

```bash
python -m unittest discover -s experiments/khepri/exp407 -p 'test_stable_drift.py' -v
python experiments/khepri/exp407/benchmark.py
python experiments/khepri/exp407/transfer.py
```

The scripts import the **current repository's** `tools.gold_walkforward`, so future upstream changes may alter the comparison. The numerical audit above was against the original function as read at the recorded SHA. Fixed-seed outputs are in `results.json` and `transfer_results.json`.

## Scope and caution

No modification was made to `tools/gold_walkforward.py`. New functions are prototypes, not integrated into `backtest`. Error metrics, display, and serialization still need independent range and finite-value audits. Extreme values are allowed by the current loader but are not realistic gold quotes; economic plausibility filtering is separate from numeric safety. This tests **numerical correctness**, not forecasting skill. No external price services were used.
