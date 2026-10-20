# Seshat c295 — direct forecast() prospective-coverage falsification

Date: 2026-10-20. Research-only; `main` unchanged.

## What changed
Prior c292–c294 experiments reconstructed evaluation logic. This experiment **directly invoked the production `forecast()` function** from `products/gold-forecast/forecast.mjs` (verified Git blob SHA `2cd3731fbb764967387270b0aeafa4ed25fafabd`), and the production `models.mjs` (SHA `6bb15abe57c87bb9bc98dbc0a25e4bff5ee65b87`). Supporting dependency modules were locally reconstructed with identical executed logic but not byte-identical blobs; this was not a GitHub CI run.

For each of 120 independent synthetic 360-day histories, the model forecast 1/7/30 observed closes ahead. The same past was paired with a stationary future (daily log-return sigma 0.4%) and a future unseen 8x volatility shock (sigma 3.2%). Future outcomes were never given to the model. 60 discovery seeds (1–60) and 60 separate replication seeds (1001–1060) were fixed before evaluation. No model tuning or threshold search was performed.

## Findings

| Set | Horizon | Mean historical coverage | Next stationary target covered | Next 8x-shock target covered |
| --- | ---: | ---: | ---: | ---: |
| Discovery | 1 | 79.91% | 73.33% | 10.00% |
| Discovery | 7 | 80.86% | 81.67% | 10.00% |
| Discovery | 30 | 77.67% | 78.33% | 13.33% |
| Replication | 1 | 81.53% | 85.00% | 20.00% |
| Replication | 7 | 81.44% | 75.00% | 13.33% |
| Replication | 30 | 73.95% | 68.33% | 16.67% |

Additional invariants: the historical-integrity adapter excluded a same-day injected price without changing forecast point, interval, or reported coverage, and rejected a future-dated price. Both assertions passed at horizons 1, 7, 30.

## Decision
A retrospective 80%-ish coverage figure is **not a prospective 80% guarantee** after an unannounced regime shift. This does **not** prove a look-ahead defect, a real-world failure rate, or that any gate can anticipate the first shock. Do not deploy any interval gate from these synthetic results.

The locally reproducible code, raw per-seed results, independent holdout and SHA256 checksums are preserved in the c295 run archive. Next: provider-vintage immutable observations and genuinely prospective issued forecasts, then stratified realized coverage by horizon/regime/publication rate. No real XAU market prices were tested; no production code was changed.
