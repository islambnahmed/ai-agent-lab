# Khepri Experiment 268 — macro-feature availability shift

Date: 2026-10-18. Offline synthetic experiment; no production modification.

## Source inspected
`products/gold-forecast/scripts/evaluate_research.mjs` already compares macro Ridge and price-only Ridge on **identical eligible origins**, with `availableFeatures(...,{maxAgeDays:120})`. This is correct for historical paired comparison. The experiment challenges a different inference: historical paired skill need not transfer if the eligible population changes.

## Fixed synthetic setup
Shock probability 20%; stable regime absolute errors (price-only, macro) = (1.0,0.7); shock errors = (4.0,6.0). A shared random positive difficulty multiplier varies errors. Historical macro availability (stable, shock) = (0.95,0.05), deployment availability = (0.70,0.80). 400 deterministic repetitions of 1,500 observations; all comparisons are same-origin paired.

## Results (seed 268)
- Historical paired gain (baseline MAE minus macro MAE): **+0.270**; deployment paired gain: **-0.215**. Sign inverted in **400/400** repetitions.
- Eligible shock fraction: historical **1.30%**, deployment **22.22%**. Break-even shock fraction **13.04%**.
- No-shift control: historical/deployment gain both **+0.270**, 0/400 sign inversions.
- Missing-at-random control: historical/deployment gain **-0.159/-0.160**, 0/400 sign inversions.
- Sparse overlap (historical shock availability 0.5%): 400/400 inversions. Poststratification lacked any historical shock support in **72/400** repetitions; among 328 estimable cases, **43** still had a misleading positive corrected sign.
- Price-only baseline all-origin MAE **~1.605**, historical macro-eligible MAE **~1.039**: eligible origins are an easier population.

## Decision / transferable lesson
Preserve the same-origin comparator. Also measure feature eligibility by volatility/regime, effective support in rare regimes, and sensitivity of paired skill to plausible deployment mix. Do not promote on retrospective complete-case skill without prospective evidence and overlap. Poststratification is only valid with supported strata and defensible deployment weights.

## Evidence and limits
10/10 standard-library Python tests passed locally. Complete reproducible code, test log, JSON results and SHA256 checksums are in the cycle's `khepri_exp268_reproducible.zip` artifact; not yet mirrored into this branch. Synthetic numbers are **not gold-market observations** and do not show that any actual source has shifted. No code in production changed.