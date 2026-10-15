# Seshat Cycle 166 — Blind audit alarm for selectively missing feedback

Date: 2026-10-15. Scope: synthetic Z/17 experiments only; no evidence of improved gold forecasts or general intelligence.

## Correction to Cycle 165

Cycle 165's learning feedback excluded the query's true answer, but its delivered-only accuracy was scored with simulator-only oracle labels. In a real deployment, that accuracy is not observable unless an independent evaluator receives the query outcome. This cycle **explicitly models a separate evaluator-only outcome channel** for delivered tasks; learners never train on that channel. A second independently sampled audit channel scores 10% of evaluation tasks, including suppressed ones.

Without any independent outcomes for suppressed tasks, true accuracy is not identifiable: a delivered correct prediction plus a suppressed unobserved prediction could represent either 50% or 100% true accuracy, with identical visible data.

## Detector (fixed before fresh evaluation)

Detector inputs: delivered-query correctness, independent audit correctness, delivery and audit indicators; **no hidden regime, suppressed truth, mask identity, or oracle accuracy**.

Alarm rule: |delivered accuracy − independent-audit accuracy| >= 10 percentage points AND a seed-cluster percentile bootstrap 95% CI (800 resamples) excludes zero. The seed is the resampling unit to preserve within-seed dependence and overlap of audited/delivered tasks. Audit sample probability = 0.10.

## Fresh seeds 4000–4029: 30 seeds × 200 eval tasks × 16 conditions = 96,000 evaluations

| Regime | Missingness | Delivered − audit (pp) | Bootstrap 95% CI | Alarm |
|---|---|---:|---|---|
| period1 | MCAR30 | +0.23 | [-1.19, 1.71] | no |
| period1 | regime_B90 | +3.96 | [1.55, 6.37] | no |
| period1 | correct_favored | +14.91 | [11.50, 18.65] | yes |
| period1 | wrong_favored | -38.88 | [-42.67, -35.30] | yes |
| period5 | MCAR30 | +1.16 | [-0.64, 3.06] | no |
| period5 | regime_B90 | +19.48 | [14.87, 24.21] | yes |
| period5 | correct_favored | +28.36 | [23.71, 33.08] | yes |
| period5 | wrong_favored | -58.12 | [-61.17, -54.48] | yes |
| markov | MCAR30 | +0.61 | [-2.68, 3.63] | no |
| markov | regime_B90 | +22.27 | [18.03, 26.41] | yes |
| markov | correct_favored | +40.04 | [36.68, 43.57] | yes |
| markov | wrong_favored | -50.56 | [-55.33, -45.68] | yes |
| iid | MCAR30 | -0.90 | [-5.38, 3.70] | no |
| iid | regime_B90 | +21.43 | [17.16, 25.59] | yes |
| iid | correct_favored | +46.08 | [41.23, 51.74] | yes |
| iid | wrong_favored | -48.55 | [-51.96, -45.22] | yes |

Audits: 591 out of 6000 evaluation tasks per condition; audit selection identical across masks per seed. **0/4 random-missingness controls flagged; 11/12 selective-missingness cases flagged.** The sole missed selective case had simulator-only true bias +6.28 pp, below the prespecified 10 pp threshold.

## Additional disjoint blocks

4 blocks × 20 seeds × 16 conditions × 200 eval tasks = 256,000 further evaluations (seeds 5000–5079). Random-missingness controls: **0/16 alarms**. Selective masks: **42/48 alarms**. Among the 43 selective condition-blocks with post-hoc oracle bias >= 10 pp, 42 were flagged. The missed case had oracle bias 10.72 pp but visible estimator discrepancy only 8.37 pp. These are synthetic blocks, not real-world error-rate guarantees.

## Verification

Local command: `python -m unittest -q test_cycle163 test_cycle164 test_cycle165 test_cycle166` — **35/35 passed**. Cycle 165 equivalence checked for world hash, delivery counts, audit counts, true accuracy, and observed accuracy. No learner receives audit labels or evaluator-only query outcomes.

Full runnable code, tests, result JSONs, and SHA256 checksums are in the conversation artifact `seshat_cycle166_blind_audit_alarm.zip` (local attachment; do not assume this branch contains those files).
- Code SHA256: `ef018ae01e4320a60049e8d97f75f67f431048942be106e3c10a71daf506d762`
- Fresh results SHA256: `2889123d1431f589def8ce1492ba6c9495bcd22cacc40dd916984eeb006a7b29`

## Limitations and next falsifier

Evaluator and audit query outcomes are assumed obtainable and simulated; no real-world collection channel was implemented. The 95% cluster-bootstrap interval is heuristic at 20–30 clusters, not a guaranteed false-positive calibration. An alarm shows disagreement, not its cause. Only the phase predictor was tested.

Next: test noisy/compromised audit labels, nonrandom audit selection, and stratified coverage; prefer access to verifiable real-world outcomes over optimizing further synthetic metrics.
