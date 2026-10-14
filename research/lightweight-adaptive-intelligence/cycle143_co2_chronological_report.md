# Seshat cycle 143 — chronological CO2 transfer audit (2026-10-14)

Status: local experiment on real timestamped weekly atmospheric CO2 values. **Feedback release lags are simulated**; real publication/vintage timestamps are not in the dataset. No gold-price or AGI claims.

## Why
Cycle 142 used real images with synthetic ordering. This experiment switches to naturally timestamped regression with chronological validation and test.

## Setup
Bundled statsmodels Mauna Loa weekly CO2: 1958-03-29 through 2001-12-29; 2,284 observations including 59 missing. Warmup 1958-1977; validation 1978-1989; untouched test 1990-2001. For target week t, predictions only use labels through t-lag-1. Missing targets skipped; no future interpolation. Hypothetical lag L means y[t] settles at t+L+1. Models: last value, 52-week seasonal, seasonal drift, rolling 156-observation harmonic trend regression, equal ensemble, and loss-weighted hedge. Hedge hyperparameters and final policy chosen on validation only.

## Test RMSE in ppm (lower better)
| Lag | Last | Seasonal | Seasonal drift | Harmonic | Equal | Hedge | Validation-selected |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 0 | 0.5261 | 1.7114 | 1.3204 | 0.6036 | 0.7788 | **0.4632** | Hedge |
| 4 | 1.5325 | 1.7114 | 1.3204 | **0.6859** | 0.8953 | 0.7070 | Harmonic |
| 12 | 3.2760 | 1.7114 | 1.3204 | **0.7871** | 1.1895 | 0.8225 | Harmonic |

Lag 0 hedge beats the best individual test expert, last observation, by 12.0% RMSE; MSE hedge-minus-last = -0.0622 ppm², 12-calendar-year paired block-bootstrap 95% interval [-0.0891,-0.0359], winning 10/12 years. Lag 4 hedge-minus-harmonic MSE +0.0293 ppm² (year-block interval [-0.0064,+0.0606], 2/12 wins); lag 12 +0.0571 ppm² ([+0.0063,+0.1131], 2/12 wins). Year blocks are not independent datasets.

## Decision
Adaptivity helped for short feedback delay on this single historical series but hurt for longer simulated delays. Validation-based policy selection avoids forcing adaptivity when a simpler model is stronger. Historical data revisions/publication vintages are unknown, so this is not a real-time-vintage audit. No claims about gold forecasts or broad intelligence.

Eight local unit tests passed (strict cutoff, no future access, lag settlement, missing targets). GitHub CI not run. Full local reproducibility bundle: cycle143_co2_prequential.py, test_cycle143.py, cycle143_results.json, REPORT_CYCLE143.md, CHECKPOINT_CYCLE143.md, SHA256SUMS.

Next: new independently dated dataset with actual vintages if possible; precommit the model selection rule and avoid more tuning on this series.