# Daily MVP gold forecast: first real-price chronological audit (2026-10-12)

## Question and method
Does the actual daily gold MVP model-selection process outperform last-close persistence on held-out historical data?

Data: 6,420 historical GOLD daily closes, 2001-06-03 to 2026-02-05, from the source described in `daily_provenance.md`. 80% earlier observations for candidate selection and final 20% for untouched chronological audit, split at **2021-02-16**. Replicated the three equations, model-selection stride and horizon logic from `feature/gold-forecast-mvp-20261008/products/gold-forecast/forecast.mjs`. This is a retrospective replication, not a live/prospective test; provenance and timezone remain uncertain. Run `node research/khepri/gold-data/backtest_mvp_daily.mjs` to reproduce.

## Findings (USD per troy ounce MAE)
| Horizon | Validation winner | Audit N | Persistence | Momentum | Mean reversion | Selected model beat persistence? |
|---|---|---:|---:|---:|---:|---|
| 1 session | persistence | 1,284 | 18.694 | 18.727 | 18.850 | No (tie: same model) |
| 7 sessions | persistence | 1,278 | 50.430 | 51.052 | 53.064 | No (tie: same model) |
| 30 sessions | persistence | 1,255 | 108.364 | 106.676 | 125.820 | No (selected persistence, despite momentum lower audit MAE) |

**Key falsification:** The monthly transfer exercise previously suggested momentum might beat persistence. On the correct **daily** input frequency, the MVP's early-period selection chooses **persistence for all 3 horizons**. A tempting post-hoc switch to 30-session momentum because its audit MAE is 1.56% better would leak test information into selection. Do not do it.

## Regime counterexample
For persistence, first vs second halves of the audit have MAE:
- 1 session: 11.966 vs 25.421 USD
- 7 sessions: 32.719 vs 68.141 USD
- 30 sessions: 65.188 vs 151.472 USD

This strongly illustrates nonstationary **absolute-dollar** errors as the gold price level/volatility changed. Compare percentage errors and evaluate calibration by regime before making claims. Overlapping multi-session targets make individual errors dependent; do not interpret N as independent evidence. Data vendor license/spot identity and point-in-time availability are not independently established.

## Decision
**Do not claim predictive edge or promote momentum from this evidence.** Next useful experiment: obtain a second independently attributable daily source, verify overlapping closes and timestamp convention, then freeze a genuinely prospective evaluation with publication-lag discipline. This cycle's result is a reproducible negative finding that prevents model-selection leakage.
