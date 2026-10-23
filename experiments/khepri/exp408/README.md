# Khepri experiment 408 — scale-invariant evaluation metrics

Date: 2026-10-24. Research-only; **no modification to main**.

## Question

Does the upstream walk-forward evaluator retain directional accuracy and RMSE when the same synthetic trajectory is expressed at different positive finite scales? Prior experiment 407 improved *forecast generation*, but did not audit the *metric computation* used by backtest.

Source: `tools/gold_walkforward.py` on main, blob `1bf63b9fce9f8d1e237f3e45b48e1bdc978e4e08` when audited.

## Confirmed counterexamples

- The current direction check multiplies `(candidate - baseline) * (actual - baseline) > 0`. With an increasing five-point series around `1e-170`, the two positive differences multiply to a value below float resolution and round to **zero**. Upstream reports direction accuracy **0.0**, while direct comparisons yield **1.0**.
- The upstream RMSE squares each residual before averaging. The same `1e-170` example reports RMSE **0.0**, although nonzero forecast errors exist. Around `1e170`, squaring finite residuals raises `OverflowError`, although RMSE is finite.
- The usual mean of `[1e308, 1e308]` overflows in the intermediate sum, despite its finite mean `1e308`. A max-normalized mean avoids this.

## Candidate

`metric_audit.py` implements strict direction using comparisons (no products), max-normalized MAE and RMSE, and a pure `summarize` function. A nonrepresentable percentage improvement returns null, not a fabricated finite percentage. Non-finite inputs or residuals are rejected. **This is a prototype, not a production patch**; upstream backtest integration, real-market data checks, and broader input validation remain outstanding.

## Evidence

- 12/12 local unit tests passed, including direct reproduction against the unchanged upstream `backtest`.
- 2,000 fixed-seed synthetic trials: 200 trajectories × 5 scales × 2 families (gold/SEO).
- At `1e-170`, upstream returned wrong direction accuracy and false zero RMSE on **200/200 trials per family** (400 each across both families).
- At `1e170`, upstream crashed on **200/200 trials per family** (400 across both families).
- Candidate: **zero** direction mismatches against exact-float Decimal comparisons across all 2,000 trials. Candidate RMSE maximum relative error against an independent 80-digit Decimal oracle was **<2.3e-16** (all trials).
- At ordinary scales, upstream did not exhibit these particular failures in the tested trials. The extremes deliberately probe numerical limits; they are not realistic prices or traffic counts and **do not estimate production failure rates**.

## Reproduction

From repository root:

```bash
python -m unittest discover -s experiments/khepri/exp408 -p 'test_metric_audit.py' -v
python experiments/khepri/exp408/benchmark.py
```

The scripts import the repository's current `tools.gold_walkforward`; results may change if it is updated. The downloadable offline archive includes an unchanged snapshot of the upstream source. `results.json` records deterministic benchmark results.

## Limitations and next step

The prototype uses float residuals, so representable input values whose difference exceeds float range are explicitly rejected rather than handled by arbitrary precision. A complete integration must handle metrics, output JSON serialization, and forecast-range errors coherently; it should also test representative real prices and prevent implausible source data separately. This experiment validates numerical *evaluation*, not forecast quality.
