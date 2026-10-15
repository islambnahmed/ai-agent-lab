# Keystone: Gold drift baseline regime stress (2026-10-16)

## Why
The walk-forward evaluator can return `evaluation_ready` once it has >=20 non-overlapping forecast windows. That threshold says nothing about model usefulness across market regimes. This experiment tests the drift candidate against the last-price (no-change) baseline.

## Reproducible setup
- 300 seeded synthetic paths **per regime** (900 paths total), each with 500 daily closes starting at 2000.
- Seed: `20261016`, Python `random.Random`, log-return volatility `0.012` daily.
- Regimes: zero log drift; constant +0.0015 log drift/day; +0.0015 for t<250, then -0.0015.
- Forecast: `backtest(rows, horizon=7, train_min=120)` from the previously locally tested numeric-stability patch (11/11 unit tests passed). Non-overlapping target windows: 54 per path.
- Metric: `100 * (baseline_mae - candidate_mae) / baseline_mae` for each path, averaged across paths.
- 95% bootstrap intervals for the **mean of path-level improvements**, 2,000 resamples, deterministic seeds `20261016 + regime_index`.

## Verified synthetic results
| Regime | Mean improvement % | Bootstrap 95% CI | Candidate wins / 300 |
| --- | ---: | --- | ---: |
| Zero drift | -1.2573 | [-1.4901, -1.0339] | 59 |
| Persistent + drift | +3.2893 | [+2.5915, +3.9504] | 216 |
| Trend reversal | -3.7233 | [-4.1883, -3.2752] | 37 |

## Interpretation
The historical-drift extrapolator has a **regime-sensitive** advantage, not a general one. It beats the no-change baseline on these persistent-trend simulations but is worse in zero-drift and trend-reversal simulations. `evaluation_ready` should not be read as `model validated`.

## Limitations
Synthetic paths are **not** real gold prices. This experiment does not estimate live profitability, account for transaction costs, validate calibration, or prove statistically independent errors. Bootstrap units are independently simulated *paths*, not the 54 correlated windows within a path.

## Recovery
Source and machine-readable results were produced locally as `gold_regime_stress.py` and `keystone_gold_regime_stress_results_20261016.json`; neither is claimed to be committed. Reproduce by generating 500 closes using `price *= exp(gauss(mu, 0.012))` with the regimes above and evaluating `backtest` per path. Next: add a frozen real-data holdout and verify provenance before promoting any accuracy claim.
