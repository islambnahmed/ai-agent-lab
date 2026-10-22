# Seshat C346 — clustered-volatility stress test (2026-10-22)

**Scope:** synthetic simulation only; no verified gold forecasting gain.

A follow-up to C345 tested whether the median's apparent robustness to isolated outliers survives dependence and clustered shocks. Fixed methods: mean, median, and 10% trimmed mean of absolute simulated returns. A 20-observation recent window is divided by an 80-observation baseline. A 1.8x scale shift begins at observation 160, with a 40-observation detection window. For each method/scenario, a pathwise alarm threshold is calibrated on 300 independent null paths; results use 300 disjoint held-out paths. Clean detection requires an alarm after the shift and none beforehand.

| Scenario | Mean clean hit | Median clean hit | 10% trimmed clean hit | Held-out null alarms (mean/median/trimmed) |
|---|---:|---:|---:|---:|
| IID | 88.33% | 61.67% | 82.33% | 7.67% / 7.33% / 7.33% |
| Isolated 2% 5x shocks | 48.67% | 52.33% | 81.33% | 3.67% / 5.33% / 6.00% |
| Persistent log-volatility (AR coefficient 0.94) | 31.67% | 24.00% | 31.00% | 6.00% / 4.33% / 5.33% |
| Persistent volatility + 4x shock bursts | 9.00% | 11.33% | 9.67% | 2.33% / 5.00% / 2.67% |

**Correction to C345:** the median is not universally best. Trimmed mean wins clearly with isolated shocks, but no simple estimator works reliably with clustered shocks. The nominal 5% alarm calibration is not an exact held-out guarantee (IID mean showed 7.67%). This is a negative-control simulation, **not** evidence of gold-market predictive skill.

Sensitivity at 1.4x/2.2x shifts: persistent volatility clean-hit mean/median/trimmed = 11.67/9.00/10.00% and 54.00/48.00/53.33%; clustered shocks = 2.67/4.67/4.00% and 13.33/27.00/21.00%.

**Verification:** 8/8 local unit tests passed; no production gold tests or CI run. Synthetic generator and tests are retained in the local C346 experiment bundle. No modifications to main.

**Next:** compare conditional-volatility-normalized alarms on an independent, licensed, verified-cadence gold series, with a precommitted alarm budget and untouched audit set. If the source cannot be authenticated, do not claim real-world performance.
