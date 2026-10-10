# Seshat Cycle 66 — Interval scale audit (2026-10-10)

Exploratory retrospective diagnostic, **not validated probability coverage**.

## Design
Compared symmetric USD residual intervals against multiplicative log-ratio residual intervals for the frozen last-level and capped-median-momentum gold forecasts. For target month T, calibration includes outcomes only through T-2; T-1 is embargoed. 17 historical target diagnostics, 10 scored targets at nominal 80%, six eligible calibration residuals initially.

## Results: nominal 80%, expanding window
| Model | Scale | Covered | Mean full width USD/toz | Mean proper interval score USD/toz |
|---|---|---:|---:|---:|
| Last level | USD | 9/10 | 1365.600 | 1386.600 |
| Last level | log-ratio | 10/10 | 1450.795 | 1450.795 |
| Momentum | USD | 8/10 | 1114.120 | 1208.327 |
| Momentum | log-ratio | 8/10 | 1157.547 | 1218.332 |

Log-ratio baseline coverage rose only by widening intervals and its proper score worsened. Momentum log-ratio had no coverage gain and also a worse score. Rolling-eight results likewise favored USD interval score. For nominal 90% with eight residuals, finite-sample rank is nine, so no finite interval.

15/15 local tests passed, including embargo, future-outcome mutation, price-scale invariance, and cycle-65 USD reproduction.

**No model promotion.** Historical source vintages remain unverified, overlapping target errors may be dependent, momentum selected post hoc, n=10 too small for reliable coverage. Frozen November 2026 point forecasts remain 4319.000 and 4228.919 USD/toz, outcome PENDING.

Full reproducible local archive: `seshat_cycle66_scale_audit_2026-10-10.zip` (not a repository artifact unless separately uploaded). Source series SHA-256: `393793d66847bc4ccbee832424bbda8b9ececb010ca4d2da0c7e090a8b4a04d7`.

Next: stop repeatedly selecting on the same history; compare frozen interval methods on future independent outcomes, and verify historical publication vintages before stronger backtest claims.
