# Seshat cycle 108 — false-positive calibration (2026-10-12)

## Question
Does increasing a HAC/Newey-West lag reliably calibrate a zero-mean forecast-improvement test?

## Reproducible experiment
Run `node products/gold-forecast/research/dependence_calibration.mjs`.
The synthetic stationary Gaussian AR(1) null uses 2,000 independent replications,
140 observations per replication, fixed seeds, and a two-sided 5% normal cutoff.
The oracle standard error uses the *known* AR(1) covariance; it is not usable for real markets.

| AR(1) rho | Oracle | HAC lag 0 | HAC lag 7 | HAC lag 14 | HAC lag 28 | HAC lag 56 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 4.95% | 5.10% | 7.10% | 8.95% | 11.05% | 18.00% |
| 0.85 | 4.20% | 58.25% | 22.55% | 17.25% | 16.50% | 22.25% |

Monte Carlo sampling error near 5% is approximately +/-0.96 percentage points (95%).
The prior C107 lag-14 17.7% false-positive result is consistent with C108's 17.25%.
Longer HAC bandwidth is not a monotonic fix: at n=140 it can make the estimate
unstable, including when rho=0. The oracle control shows the generator is calibrated
when its true dependence is known.

## Decision
Do not interpret HAC z > 1.96 as reliable proof of live gold forecast skill.
Use prospective, time-anchored receipts, an a priori horizon and test design,
and independent robustness checks before any skill claim.
Avoid further cycles optimizing this synthetic metric without real forecasts.

## Verification
The research script and this note are on a dedicated branch. Existing GitHub
Gold Lab and AI Agent Lab CI passed for the script commit; the new script's
self-test ran locally, but is not included in CI because a workflow/test-file
write was blocked. The code is not merged into main.
