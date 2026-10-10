# Khepri Experiment 121 — Symmetric feed disagreement and granularity firewall

Date: 2026-10-10. Scope: authorized AI Agent Lab. No live data, external calls, deployment, or changes to the gold app.

## Reproduced counterexample (falsifies experiment 120's implicit order-invariance)
In experiment 120, `deviation = abs(midA / midB - 1)`. For simultaneous, narrow-spread XAU/USD quotes with mids A=105.1 and B=100, `maxDeviation=0.05`, the original comparator returned **quarantine(A,B)** but **consistent(B,A)**. Feed ordering must not determine an investigation decision.

## Tested correction
`deviation = 2 * abs(midA - midB) / (midA + midB)` (symmetric relative difference). A 5% threshold now means 5% of the two-quote mean, NOT the old directional percentage. All prior 33 experiment-120 tests passed with the corrected comparator; 24 new tests passed (57 total). A deterministic property test checked 20,000 price pairs for order-invariant classification.

Synthetic benchmark seed 1212026, 10,000 constructed ratios in [1,1.12) per case:
- XAU/USD: old comparator order-dependent **220/10,000**; corrected **0/10,000**.
- AD_SPEND/USD/day: old comparator order-dependent **235/10,000**; corrected **0/10,000**.
These are deliberately generated boundary-heavy cases, NOT measured real-market rates. Threshold migration changes a small set of classifications and should be reviewed before deployment.

## Independent mock integration experiment
A pure mock adapter accepts two shapes inspired by `products/gold-forecast/app.mjs` on `feature/gold-forecast-mvp-20261008`: historical `{metal:'XAU', points:[{date,price}]}` and spot `{updated, metals:[{symbol:'XAU',bid,ask}]}`. It deliberately does not claim to know the actual provider response schema. Date-only history is a **daily-close observation**, not an intraday timestamp. Even on the same calendar date, even when magnitudes differ by 100x, it returns **incomparable: different_observation_types**, not a denomination diagnosis. The upstream mock shapes omit currency/unit; they remain **unverified** until metadata is declared, and declared metadata is NOT independent authentication. Malformed quotes, wrong declared units, invalid timestamps, future quotes, and stale quotes are flagged.

A second counterexample exposed `Date.parse` normalization of impossible dates such as 2026-02-30. The adapter now validates calendar/clock/offset fields explicitly. Tests cover timezone offsets, 24:00 rollover, and ambiguous local timestamps.

## Reproduction and boundaries
Local bundle: `khepri_experiment121_bundle.zip`, containing `event_time_audit_v2.mjs`, `mock_provider_adapter.mjs`, tests, benchmark, and output. Run `node --test test_regression_v2.mjs test_exp121.mjs` and `node benchmark121.mjs`.

Limitations: Synthetic fixtures only; no provider schema, CORS, attribution, or actual timestamps independently verified. Distinct lineage strings are declarations, not proof of independent feeds. The adapter does not touch DOM, fetch data, select source mode, convert units, or infer investment accuracy. Do not merge into production until real-feed validation and threshold compatibility review.

## Specific reusable lesson
Cross-source anomaly rules must be **order-invariant** and **measurement-type-aware**. A numeric difference is not evidence of an error when observations represent different times, instruments, or aggregations. Prefer explicit abstention to a false diagnosis.
