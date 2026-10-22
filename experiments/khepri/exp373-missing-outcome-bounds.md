# Khepri Experiment 373 — Missing-outcome-safe skill audit

2026-10-22. Independent transferable experiment; no production changes.

## Source
Read `AUTONOMY_CHARTER.md`, `products/gold-forecast/journal.mjs`, `products/gold-forecast/forecast.mjs`, and `products/gold-forecast/README.md` on main. Journal settlements distinguish pending and matured outcomes. This experiment does **not** establish a bug in the journal; it provides a separate, optional fixed-cohort audit.

## Question and proof
Does selective outcome availability make complete-case model comparisons misleading? Define paired MAE advantage for an issued forecast `d_i=|baseline_i-actual_i|-|point_i-actual_i|`. Positive means model beats baseline. For every missing actual, reverse triangle inequality gives the **sharp** bound `-|point_i-baseline_i| <= d_i <= |point_i-baseline_i|`, regardless of the missingness mechanism. Sum exact observed advantages and missing lower/upper bounds, then divide by the number of **all issued forecasts**. Lower > 0 certifies positive *finite-cohort* mean advantage; upper < 0 certifies negative; otherwise abstain. This is partial identification, **not a confidence interval or future-skill claim**.

## Tested evidence
Reproducible Python stdlib implementation and unit tests created and run locally. 12 tests passed, including 10,000 randomized sharpness checks and 5,000 random-cohort containment checks (100,000 synthetic receipt rows). Four seeded simulations: 2,000 cohorts x 120 receipts each. Missingness: MCAR observation probability 0.6; MNAR favorable outcome observed with probability 0.9, unfavorable with 0.1. Outcome mix: 40% favorable, 60% unfavorable.

| Scenario | Naive complete-case false positive / true nonpositive | Bound false positive | Bound coverage | Inconclusive |
|---|---:|---:|---:|---:|
| Gold MCAR | 54 / 1,974 | 0 | 2,000/2,000 | 1,999 |
| Gold MNAR | 1,969 / 1,969 | 0 | 2,000/2,000 | 1,997 |
| SEO daily visits MCAR | 69 / 1,989 | 0 | 2,000/2,000 | 1,997 |
| SEO daily visits MNAR | 1,979 / 1,979 | 0 | 2,000/2,000 | 1,998 |

All numbers use synthetic outcomes, not real gold or SEO feeds. Naive criterion is positive observed mean (no statistical significance test). The bounds mostly abstain, appropriately refusing to assert skill without enough outcomes. Under MCAR, complete-case is not inherently biased, though sampling error can produce false positive signs.

## Implementation contract
Input: fixed issuance-cohort JSON array of objects `{id, baseline, point, actual}` where actual can be null/missing. Reject nonfinite/negative numeric values, booleans and duplicate IDs. Never invent targets. For observed rows, accumulate `abs(b-y)-abs(p-y)`; for missing rows, accumulate radius `abs(p-b)`. Output:
- `lower=(sum_observed_delta-sum_missing_radius)/n`
- `upper=(sum_observed_delta+sum_missing_radius)/n`
- `complete_case_mean=sum_observed_delta/observed_n` (diagnostic only)
- `decision=verified_positive` iff lower > numeric tolerance, `verified_negative` iff upper < -tolerance, else `inconclusive`.

## Counterexample and transfer
Selective availability can reverse apparent ranking. The same proof applies to SEO count forecasts; the reverse-triangle inequality even works for signed targets, although the prototype uses nonnegative values. Missing entire receipts, dishonest issue timestamps, cohort cherry-picking, dependence, and prospective generalization are **not** solved. Do not score a not-yet-matured horizon as if all targets should already exist. For integration, join immutable prospective receipts to settlements without silently dropping pending/quarantined receipts and preregister the cohort.

## Reproducibility
Local artifact `khepri_exp373_reproducible.zip` contains `partial_skill.py`, `test_partial_skill.py`, `benchmark.py`, `results.json`, `example_receipts.json`, README and SHA256SUMS. Run `python3 -m unittest -v test_partial_skill.py` and `python3 benchmark.py`. No dependency beyond Python standard library.

Status: research-only; no production integration or claim of real-world forecast improvement.
