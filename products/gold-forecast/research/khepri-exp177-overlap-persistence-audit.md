# Khepri Experiment 177 — Overlap-aware inference breaks under persistent shocks

**Date:** 2026-10-14. **Scope:** synthetic falsification benchmark, NOT observed gold returns or verified gold-model improvement. **Branch:** `khepri/exp177-persistent-overlap-20261014`.

## Research question
Experiment 176 found inflated false-positive rates when paired forecast errors share overlapping horizons. Can prespecified nonoverlapping evaluation origins restore a 5% false-positive rate, and does that survive persistent underlying shocks?

## Method
Simulate 240 paired loss differences per replication: `d_t = (epsilon_t + ... + epsilon_(t+h-1))/sqrt(h) + delta`. Gaussian innovations are either independent or stationary AR(1) with rho 0.8 or 0.95. Compare (1) naive Student t on all 240 differences, (2) Bartlett HAC with h-1 lags and normal cutoff, (3) Student t using fixed origin phase 0 every h origins, (4) Student t using fixed origin phase 0 every 2h origins. Two-sided alpha 0.05; 3,000 independent Monte Carlo replications per condition. Also assess power under iid innovations with delta=0.5. Fixed phase means no ex-post selection of a favorable offset.

## Verified simulation results
Each number is **percentage of replications rejecting the null**, with nominal 5% under delta=0; under delta=0.5 it is power.

| h | rho | delta | Naive | HAC h-1 | stride h | stride 2h |
|---:|---:|---:|---:|---:|---:|---:|
| 7 | 0 | 0 | 46.1 | 12.3 | 5.1 | 5.1 |
| 7 | 0.8 | 0 | 60.9 | 22.7 | 16.6 | 6.8 |
| 7 | 0.95 | 0 | 77.9 | 47.9 | 44.8 | **26.1** |
| 30 | 0 | 0 | 73.2 | 18.8 | 4.9 | 4.9 |
| 30 | 0.8 | 0 | 75.7 | 19.9 | 6.8 | 4.4 |
| 30 | 0.95 | 0 | 81.5 | 30.6 | 15.5 | 6.2 |
| 7 | 0 | 0.5 | 98.8 | 91.8 | 83.5 | 51.8 |
| 30 | 0 | 0.5 | 90.3 | 51.2 | 24.6 | **13.4** |

For h=30, stride h retains only 8 observations and stride 2h retains **4**, so apparent calibration at 2h does not mean useful evidence. For h=7 with rho=0.95, even 2h separation produces a 26.1% false-positive rate. Correlation across nominally disjoint windows is the counterexample.

## Decision
**Reject** the claim that nonoverlapping forecast windows are automatically independent. **Do not** promote HAC(h-1) or fixed-stride tests as universally calibrated. Require a preregistered dependence model/sensitivity audit, sufficient effective sample size, and prospective out-of-sample evidence before announcing model superiority. If those are unavailable, return **inconclusive** rather than a significance claim.

## Reproducibility
Local reproducible bundle `khepri_exp177_reproducible.zip` contains `audit.py`, `test_audit.py`, `results.json`, and this report. Dependencies: numpy/scipy. Command: `python -m unittest -v test_audit.py && python audit.py --trials 3000 > results.json`. **12/12 tests passed**. 8 Monte Carlo conditions × 3,000 = **24,000** independent simulated series; these are simulations, not real gold forecasts. The earlier baseline experiment 176 was read locally and this experiment directly challenges its inference assumptions.

## Limitations
Synthetic Gaussian moving sums; fixed rho, fixed n, selected horizon lengths. The 5% target is a null-model benchmark, not a guarantee under nonstationarity, heavy tails, selective outcomes, or model selection. The AR(1) innovations begin from their stationary marginal but are not burn-in sampled; negligible edge effects are possible. Need original paired loss series and publication-time verification to assess actual gold models. No production model or main branch modified.
