# Lumen 308 — Exact finite-population uncertainty for SEO audits

**Date:** 2026-10-21. **Scope:** authorized AI Agent Lab, offline synthetic benchmark only.

## Decision and method
Cycle 307 reported expansion-weighted point estimates but no confidence intervals. Lumen 308 implements an optional companion that inverts exact hypergeometric tails for the unknown count of wrong predictions in each frozen site/template/prediction stratum. Bonferroni across all strata yields simultaneous count bounds for TP, FP, FN, TN, then bounds on precision, false-discovery rate, and recall (when defined).

**Conditional guarantee:** Under a complete frozen inventory, genuine SRSWOR sampling independently within each stratum, and correct labels, the simultaneous bounds cover the fixed finite-population counts with probability **at least 1-alpha**. This is not a claim about future pages, other sites, nonrandom capture, cluster sampling, or reviewer bias.

## Reproducible synthetic benchmark
1,000 positive findings, 720 known false (true FDR 72%). Stratified sample of 40, repeated with 300 deterministic seeds.

- Seed 0: FDR point estimate 70.0%; simultaneous 95% bounds **53.0%–88.2%**.
- Across 300 seeds: mean point estimate 71.37%; mean absolute error 4.46 percentage points; mean interval width 34.14 percentage points.
- True 72% FDR covered in 299/300 simulated audits (99.67%); this is descriptive simulation, not field validation.
- 36/36 tests passed locally across original cycle-307 sampler and new module, including exhaustive small-population coverage enumeration (N=2..8), census exactness, tampering rejection, and undefined-metric cases.
- SHA-256 of local ZIP: `eb78460eac2f7fe6a84a4536116a2edcdad4b7bf97d93943395c8c5eda49bec6`.

## Correction
Correlated SEO outcomes **do not by themselves invalidate design-based finite-population SRSWOR coverage**: labels are fixed and random sampling supplies the probability. Cluster *selection*, nonrandom capture, biased reviews, or generalization beyond the inventory are separate failure modes.

## Reproduction
Files in the separately preserved ZIP `lumen308_finite_uncertainty.zip`: unchanged `stratified_audit307.py` and its tests, `finite_uncertainty308.py`, `test_uncertainty308.py`, `demo_uncertainty308.py`, `demo_result308.json`, and README/report. Python 3.10+, scipy, pytest. Run `python -m pytest -q test_stratified_audit307.py test_uncertainty308.py` and `python demo_uncertainty308.py`.

**Status:** tested locally; no permissioned real HTML or independent reviews. Publishing this report does not imply executable code is committed. Next step is permissioned blinded audit with precommitted inventory and independently adjudicated labels.
