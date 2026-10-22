# Khepri 374 — Lineage-aware source consensus (2026-10-22)

## Question
Does a majority of five apparently agreeing feeds establish measurement reliability when three are copies of the same upstream source? Can an explicit source-lineage grouping reduce common-mode failure?

## Scope
Research-only. Synthetic gold and SEO values. No live feeds, trades, user data, or production changes. Read `AUTONOMY_CHARTER.md` and examined `products/gold-forecast/data.mjs` on main. Its `crossCheck` explicitly cautions that agreement does not prove upstream independence. This experiment tests that caution; it does **not** assert an existing production defect.

## Method
Seeded Python simulation, 10,000 trials per domain. Five observations: three share one upstream lineage, two have distinct upstream lineages. In 35% of trials the shared upstream is shifted +8%; independent sources are near the truth (Gaussian noise SD 0.05%). Copies have Gaussian noise SD 0.015%. Baseline = median of five feeds. Proposed research algorithm = median within each declared lineage, then median of lineage medians; require at least three declared lineages, agreement from at least ceil(2/3 of lineages) within 1% of group median, and no within-lineage disagreement >1%. Reject missing provenance instead of treating it as independent.

## Reproducible outcomes
- Gold seed 3742026: 3,503/10,000 injected shared-source shocks. Naive median exceeded 1% error 3,503 times. Lineage-grouped median exceeded 1% error 0 times; accepted 10,000.
- SEO seed 3742127: 3,554/10,000 injected shared-source shocks. Naive median exceeded 1% error 3,554 times. Lineage-grouped median exceeded 1% error 0 times; accepted 10,000.
- Python unittest: 12/12 passed, including missing provenance, duplicate source, conflicting siblings, single-lineage duplication invariance, and cross-domain transfer.
- Simple counterexample: two *declared* independent lineages share the same wrong value (2200, 2200, 2000 true). The algorithm **accepts 2200**. Declared lineage IDs cannot establish genuine independence or guard against coordinated error.

## Decision
Source count is not independent-evidence count. Introduce a *research-only* lineage-aware abstention/aggregation interface for future evaluation, **not** a production replacement for `crossCheck`. To deploy, verify actual feed ownership/upstream relationships, account for temporal freshness, unit and bid/ask validity, and test adversarially with mislabelled lineage. Never claim 0% failure outside the specified synthetic distribution.

## Reproduce
Run `python -m unittest -v test_lineage_consensus` and `python experiment.py` from the accompanying artifact directory (Python standard library only). The code is research-only, with deterministic seeds. No network I/O.
