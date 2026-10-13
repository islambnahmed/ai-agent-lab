# Lumen: Gold forecast calibration uncertainty audit — 2026-10-13

## Source and reproducibility
Source: `products/gold-forecast/reports/readiness-20261012.json` on `main`, fetched 2026-10-13. This is a **retrospective reconstruction** based on a current-vintage history, not a prospective validation result. The report's `horizon` counts **future observed provider closes**, not fixed calendar days.

## Diagnostic: selected non-overlapping phase only
| Horizon (observations) | Model | Overall overlapping coverage | Phase-0 coverage | Wilson 95% illustrative interval (phase 0) | Phase coverage range | MAE skill on overlapping audit |
|---|---|---|---|---|---|---|
| 1 | persistence | 59/65 (90.77%) | 59/65 (90.77%) | 81.29%–95.70% | 90.77% | 0.00% |
| 7 | mean_reversion | 46/59 (77.97%) | 7/9 (77.78%) | 45.26%–93.68% | 50%–87.5% | -3.06% |
| 30 | momentum | 32/36 (88.89%) | 2/2 (100%) | 34.24%–100% | 0%–100% | -14.33% |

**Important:** Wilson intervals assume iid Bernoulli coverage outcomes. That assumption has NOT been established for financial forecast errors, and the source itself warns that non-overlapping target windows are not statistically independent. These intervals are *illustrations of sample-size uncertainty*, not validated 95% coverage confidence intervals for this system. Phase offsets share many of the same origins and must not be pooled as independent observations.

## Finding
The attractive 30-observation 88.89% aggregate coverage hides a phase-0 count of only **2**. Both phase-0 intervals covering the truth cannot establish 90% calibration; even the illustrative iid Wilson lower endpoint is 34.24%. Other 30-observation phase offsets have 0% coverage. The overlapping MAE skill is negative (-14.33%) relative to persistence, so there is no demonstrated superiority on that horizon. The 7-observation phase-0 result (7/9) is similarly too sparse for robust calibration claims, and its overlapping MAE skill is also negative.

## Guardrails for future decisions
1. Keep overlapping audit, phase-0 descriptive counts, and all phase-offset sensitivity distinct; do not report any of them as independent prospective trials.
2. Never choose the most favorable phase offset after seeing results.
3. Log immutable future forecasts, source-vintage data, origin timestamp, target-observation definition, and actual resolution before computing prospective performance.
4. Compare prospective MAE against a pre-registered persistence baseline, with uncertainty assessed using a dependence-aware method only after enough resolved origins exist.
5. Mark calibration and skill **unproven** until prospective evidence exists. Do not promote a model based on this audit.

## Verification
Readiness report fetched through authorized GitHub connector. Computed exact phase hit counts by checking integer consistency of the reported percentages. Local dependency-free Node.js utility and **10 passing tests** were prepared. Direct raw.githubusercontent.com access from the local execution container failed DNS resolution, so full end-to-end local ingestion of the remote report was not verified; numeric diagnostics above were computed from the GitHub connector's live report response.

This is an advisory diagnostic, not a production code change.