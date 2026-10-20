# Khepri Exp324 — Causal isolated-spike detection (2026-10-20)

**Research-only synthetic benchmark.** No live gold data, no production changes.

## Why
Exp323 showed that Exp322's GARCH shock detector was detecting variance propagation rather than isolated shocks. This cycle constructed a counterfactual benchmark with the exact same null GARCH path except for a single value x[240]=20, plus a separate *stationary* post-hoc 3x scale shift.

## Reproducible design
- Gaussian and standardized Student-t3 GARCH(1,1), alpha=.16, beta=.81; 200 train + 120 monitor observations, change at monitor index 40.
- 2,000 null episodes/family for component calibration (seed 8240000); separate 2,000 null episodes/family for joint conformal calibration (seed 8340000).
- Independent final validation: **3,000 episodes per family and regime**, seed 10240000 (+100000 family offset).
- Scores: legacy winsorized RMS + extreme-pair, raw absolute observation / fixed training median, local absolute observation / previous-40 median, 3-component Bonferroni, and split-calibrated 2-component joint OR of raw peak + winsorized RMS.
- A first alarm **at change index 40 or 41** counts as immediate spike detection; an earlier false alarm disqualifies it. False alarm is any alarm in a 120-observation null episode.
- The conservative joint alpha=.035 option was selected *after* inspecting a development set (seed 9240000), and tested on a disjoint validation set. Do not call it preregistered.

## Independent validation (n=3,000/case)
| Null family | Policy | Null episode false alarms | Isolated spike immediate detection | Stationary 3x shift first-post detection |
|---|---|---:|---:|---:|
| Gaussian GARCH | Legacy hybrid | 3.10% | 0.07% | 45.70% |
| Gaussian GARCH | Raw peak | 0.03% | 77.13% | 3.07% |
| Gaussian GARCH | Joint OR nominal 5% | 5.23% | 76.80% | 61.83% |
| Gaussian GARCH | Joint OR guarded 3.5% | 1.00% | 59.73% | 22.70% |
| Student-t3 GARCH | Legacy hybrid | 2.37% | 0.10% | 24.77% |
| Student-t3 GARCH | Raw peak | 4.53% | 97.97% | 30.47% |
| Student-t3 GARCH | Joint OR nominal 5% | 4.97% | 97.93% | 37.07% |
| Student-t3 GARCH | Joint OR guarded 3.5% | 3.80% | 98.10% | 25.27% |

**Important:** nominal 5% conformal controls marginal episode probability under exchangeability, not every finite sample's realized false-alarm rate. Development-set joint FPR was 5.40% / 5.55%; validation was 5.23% / 4.97%. This is not a distribution-free guarantee under live market drift.

## Falsification / transfer
Unchanged gold-calibrated thresholds were transferred to standardized synthetic website-visit residuals (800 episodes/family/case). Joint OR detected 100% of injected 600-count spikes under Poisson, but only **32.25%** under overdispersed negative binomial. Zero null alarms were seen in these 800 runs in either website family, reflecting overconservatism rather than proving calibration. Website 'vol3' is a bursty gamma-Poisson mixture, not the stationary GARCH scale shift.

## Lesson
Adding a raw peak score recovers the isolated-spike blind spot. Combining it with winsorized RMS helps sustained scale shifts, but conservative calibration reduces both false alarms and useful power. Family misspecification matters. No production deployment is justified without live-data provenance, leakage-free time splits, and a realistic trading/observation calendar.

## Evidence and limitations
14 unit tests passed, including paired-path identity, no lookahead, first-alarm scoring, split calibration, and website transfer. Full runnable bundle: `khepri_exp324_reproducible.zip` generated in the conversation working directory (not claimed uploaded to GitHub). It includes `isolated_spike_benchmark.py`, `website_transfer.py`, `test_isolated_spike.py`, Exp320–322 dependencies, all calibration/evaluation results and logs. This GitHub report does **not** assert that the executable files are committed here unless separately verified.
