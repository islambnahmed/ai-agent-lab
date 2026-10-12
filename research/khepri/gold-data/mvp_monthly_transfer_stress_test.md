# Khepri: actual MVP forecast formulas on historical monthly gold (exploratory, 2026-10-12)

Source: `research/khepri/gold-data/gold_monthly_1960plus.csv`, 801 monthly prices. MVP implementation inspected at `feature/gold-forecast-mvp-20261008/products/gold-forecast/forecast.mjs`. **The MVP is built for DAILY closes and h=1/7/30 trading sessions.** The experiment below directly applies its three prediction formulas to MONTHLY averages and interprets h as 1/3/6 monthly steps. Therefore these numbers are **not** a valid score of the deployed daily model. They are a transfer/stress test of model formulas only.

Chronological holdout: Jan 2023–Sep 2026; each origin predicts the current month from preceding months only. For h>1, targets are i+h-1. Prediction formula uses no target data. Data-publication lag not verified; monthly averages may be released after month end, so even this illustrative exercise is not a certified point-in-time trading backtest.

| Horizon (months) | N | Persistence MAE USD | Momentum MAE USD | Mean reversion MAE USD |
|---|---:|---:|---:|---:|
| 1 | 45 | 112.24 | 109.59 | 118.00 |
| 3 | 43 | 266.37 | 251.82 | 297.43 |
| 6 | 40 | 472.03 | 444.43 | 529.66 |

**Finding**: The fixed MVP momentum formula beat persistence on this selected recent monthly period, but only by 2.4%, 5.5%, and 5.8% MAE respectively; mean reversion lost. This is not evidence of robust skill because (a) daily-model formulas were transplanted to monthly data, (b) the holdout was chosen retrospectively, (c) no uncertainty estimate, (d) time-varying market regime, (e) publication timing, and (f) overlapping multi-month targets.

**Counterexample**: In a 2016–Sep 2026 one-month baseline experiment, simple persistence MAE=63.23 USD while 3-month drift MAE=67.56; longer and more recent evaluation windows can reverse rankings. Need point-in-time DAILY observations with license, then run unchanged daily MVP `forecast()` selection and truly frozen prospective holdout. No deployment or claim of alpha.
