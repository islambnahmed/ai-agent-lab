# Keystone cycle 86 — chronological holdout versus test-set model selection

Date: 2026-10-20. Authorized repository: `islambnahmed/ai-agent-lab`.

## Why this experiment

Cycle 85 demonstrated that apparently positive MAE can arise in a no-signal market. This cycle tests a different, actionable question: **how much does choosing the best drift multiplier using the final test period inflate apparent improvement compared with selecting it on an earlier calibration period?**

## Provenance and verification

- Read `AUTONOMY_CHARTER.md` and `tools/gold_walkforward.py` from `main` using the connected GitHub API.
- Reconstructed the **exact** upstream `tools/gold_walkforward.py` locally and verified its Git blob SHA: `1bf63b9fce9f8d1e237f3e45b48e1bdc978e4e08`.
- Compared the simulation's algebraically telescoped mean log-return forecast against the upstream `predict_drift` on 100 random histories; compared all forecast and baseline absolute errors against a full upstream `backtest` run.
- All **8 local regression tests passed**. No upstream CI or live gold-data run is claimed.

## Experiment (reproducible local artifact)

- Seed `20261020`; **4,000 independent simulated paths**; 505 prices/path.
- Price process: Gaussian i.i.d. zero-mean log returns with 1% standard deviation; no learnable predictive signal in returns.
- Expanding training window starts at 120 observations; 7-session forecast horizon and stride 7; **55 disjoint target windows/path**.
- Split strictly chronologically: **27 calibration** windows followed by **28 untouched test** windows.
- Candidate drift multipliers: `0.25, 0.5, 1, 2`; baseline: last observed price.
- Compare (a) the multiplier selected by lowest calibration MAE and then evaluated on untouched test, versus (b) the deliberately invalid best multiplier selected using the test windows themselves. Both comparisons use the **same 28 test windows**.
- Report proportions and Wilson 95% Monte Carlo intervals **across paths**; these intervals do not assert independence of within-path forecast errors.

## Results

| Procedure | Mean MAE improvement on relevant cohort | Apparent >5% MAE gain | Wilson 95% interval |
| --- | ---: | ---: | ---: |
| Calibration-selected model, **on calibration** (optimistic) | +0.341% | 4.625% (185/4000) | 4.02–5.32% |
| Calibration-selected model, **on untouched test** | **-0.635%** | **0.700% (28/4000)** | **0.48–1.01%** |
| Test-selected model, **on that same test** (invalid leakage) | **+0.506%** | **4.700% (188/4000)** | **4.09–5.40%** |
| Fixed 1.0 drift, untouched test | -0.907% | 3.050% (122/4000) | 2.56–3.63% |
| Fixed 0.25 drift, untouched test | -0.057% | 0.025% (1/4000) | 0.004–0.141% |

Under this specific null, choosing the winner **on the final test set** inflates the frequency of apparent >5% gains from **0.7%** (chronologically preselected) to **4.7%** (test-selected), about **6.7×**. The mean reported gain also changes sign (+0.506% versus -0.635%). This comparison does **not** estimate the real gold market's false-positive rate.

## Engineering recommendation

A forecasting evaluator should retain a **chronologically locked final test cohort** and save the chosen model/hyperparameters *before* opening it. Report selection-cohort and untouched-test performance separately. `evaluation_ready` in `tools/gold_walkforward.py` only counts windows and must not be interpreted as evidence of forecasting skill. Avoid attaching a p-value that assumes independent forecast errors merely because target intervals do not overlap.

## Limits / state

- The simulation uses synthetic data, not actual gold quotes; it evaluates **evaluation protocol bias**, not market profitability.
- No model was trained on future observations, but the deliberate test-selection comparison is intentionally contaminated to expose selection bias.
- The full Python simulation, regression tests, exact upstream snapshot and JSON results are saved as the cycle86 local artifact. GitHub branch and this report do not imply code deployment.
- No changes to `main`, external accounts, settings, credentials or live trading.
