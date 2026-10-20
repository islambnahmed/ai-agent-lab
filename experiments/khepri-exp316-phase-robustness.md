# Khepri Experiment 316 — Phase robustness of pooled forecast MAE

Date: 2026-10-20. Research only; no production edits.

## Question and inspected code
`products/gold-forecast/forecast.mjs` calculates pooled audit `beat` from candidate vs persistence MAE, and reports non-overlapping origin-phase *coverage* but not per-phase candidate/baseline MAE or leave-one-phase-out skill. The README already correctly states disjoint windows are not statistically independent.

The committed `reports/readiness-20261012.json` (324 source observations through 2026-10-11) has disjoint audit counts of **65** (h=1), **9** (h=7), and **2** (h=30). With auditStart=floor(324*0.8)=259, h=30 has **36 overlapping origins**, leaving only **1–2 observations per phase**. The selected 30-close model had **-14.33%** published audit MAE skill; no claim of positive real-world skill is made.

## Falsifying counterexample (synthetic)
Construct 60 origins at h=30. Baseline absolute error=10 for every origin. Candidate error=0 for the two origins in one phase; candidate error=10.2 for the other 58 origins.

* Pooled candidate MAE **9.86** vs baseline **10.00**; apparent pooled skill **+1.40%**.
* Candidate wins **1/30 origin phases** and loses **29/30**.
* Removing the single winning phase reverses skill to **-2.00%**.
* Each phase has just 2 origins; phase cohorts are not independent.

Therefore pooled `beat` alone does not establish phase-robust superiority. This does not prove the selector is incorrect, and phase majority is not a significance test.

## Transfer and reproducibility
The same deterministic experiment at horizon 7, with values scaled 10x to represent synthetic web-traffic counts, retains pooled skill and winning-phase fraction. This is structural transfer, not evidence from real traffic.

A standard-library Python phase auditor and 14 passing unit tests were executed locally. The auditor reads the `forecast(...,{includeRows:true})` JSON audit/baseline arrays, pairs on originIndex, validates matched actuals, rejects nonfinite prices, and reports phase MAE/skill and leave-one-phase-out sensitivity. The reproducible bundle was generated locally in this cycle; the repository report intentionally does not claim that the code was uploaded.

## Caveats / next test
No unpublished provider prices or raw audit rows were available. The counterexample is synthetic. Phase win fraction is descriptive, not a probability/p-value. With only 1–2 origins per h=30 phase, sensitivity estimates themselves are noisy. Next: export matched prospective audit rows after outcomes mature, run a preregistered phase audit, and do not promote a model on this evidence alone.
