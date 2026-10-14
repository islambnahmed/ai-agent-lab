# Seshat Cycle 165 — Informative Missingness Audit

Date: 2026-10-15. **Synthetic finite-field Z/17 experiment; no claim of gold-forecast improvement or general intelligence.**

## Research question
Cycle 164 showed strong phase-expert results under random missing feedback. Can selectively suppressed feedback cause measured performance to diverge from the accuracy of all predictions? Can an independently randomized audit expose the discrepancy?

## Causal protocol
- Reused cycle 164 world generator, 4 predictors (strict, last_received, phase, phase_guard), 60 training + 200 evaluation tasks per seed, feedback at t+4.
- Four masks: MCAR30 (70% delivered), regime_B90 (10% of hidden B vs 90% of others delivered), correct_favored (95% delivered when phase is correct, 5% otherwise), wrong_favored (the reverse).
- The last two masks use oracle correctness **only in the simulated environment to choose delivery**. No oracle labels, hidden regime or dropped feedback enter any predictor.
- A separate RNG selects 10% of evaluation tasks for **audit-only** scoring regardless of delivery. Audit results never train a learner.
- Frozen predictions are scored only after the relevant delayed feedback arrives; queued messages after the prediction horizon are included only in retrospective audit, never used to update a learner.
- 30 seeds (3000–3029), 4 scenarios × 4 masks × 200 eval tasks = **96,000 evaluated tasks**, plus 28,800 training tasks. World hashes identical across masks for a seed.

## Selected results (mean accuracy %, 30 seeds)

| Scenario / mask | All predictions | Delivered only | Independent 10% audit | Delivered minus all (pp) |
|---|---:|---:|---:|---:|
| Period5 / MCAR30 | 92.20 | 91.63 | 91.31 | -0.57 |
| Period5 / regime_B90 | 74.12 | 89.38 | 73.91 | +15.26 |
| Period5 / correct_favored | 75.52 | 98.20 | 73.32 | +22.69 |
| Period5 / wrong_favored | 91.28 | 37.37 | 91.20 | -53.92 |
| IID / regime_B90 | 57.62 | 78.74 | 56.06 | +21.13 |
| IID / correct_favored | **52.83** | **94.97** | **53.59** | **+42.14** |
| IID / wrong_favored | **57.65** | **7.40** | **55.59** | **-50.25** |
| Markov / correct_favored | 56.05 | 95.75 | 57.29 | +39.70 |

Approximate 95% seed-level intervals for observed-only bias: IID/correct_favored [+40.33,+43.95] pp; IID/wrong_favored [-51.54,-48.97] pp. Audit is noisy (~20 sampled tasks/seed), and finite-sample audit estimates can deviate from truth; in Markov/wrong_favored the mean audit estimate was 4.51 pp below true accuracy.

## Decision
**Feedback-dependent evaluation is unsafe as an accuracy metric without missingness assumptions.** Even when underlying world tasks are identical across masks, selective delivery both changes learning and distorts delivered-only metrics. An independent random audit is a better diagnostic, but requires independently obtainable ground-truth labels. Coverage by observable subgroup should be reported, with unobserved strata explicitly unverified.

## Verification
Local command: `python -m unittest -q test_cycle163 test_cycle164 test_cycle165` — **28/28 passed**. Same-world fingerprints, deterministic results, frozen forecasts, no future leakage, independent audit selection, and no training from audit labels tested.

**Limits:** synthetic programmer-generated grammar and missingness; 10% audit variance; no real-market validation. Reporting seeds were rerun after adding the audit and correcting horizon censoring, so they are **not a pristine untouched final holdout**. No learner hyperparameters were tuned on these seeds.

## Artifacts and next falsifier
Full executable code, regression tests, per-seed results, and SHA-256 checksums: `seshat_cycle165_mnar_audit.zip` attached in the automation conversation (local artifact; not yet in this GitHub branch). Code SHA256: `dd33b578dfe2d3ebeec41c8d24173545bfb8a2e799e2dfe4f88c8feee2649606`. Results SHA256: `35de3b1589aedbc31962a49fb0124bd70ff6e9a52df78539ac2ef85da43210c2`.

Next: preregister non-oracle coverage and randomized-audit discrepancy alarms, test on fresh seeds, and evaluate whether alarms work when missingness is regime-dependent rather than correctness-dependent.