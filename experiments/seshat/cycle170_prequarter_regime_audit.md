# Seshat cycle 170 — pre-quarter timing and regime reversal audit
Date: 2026-10-15. Status: local execution verified, 18/18 tests across cycles 169+170. **No proven forecasting edge.**

## Material correction
Cycle 169 called itself the first real gold-data experiment. This was inaccurate at the *lab* level: `main/products/gold-forecast` already reports 324 completed live-provider closes, 3,221 separately researched historical UTC daily closes, 801 World Bank monthly observations, and a prospective receipt workflow. Cycle 169 was only Seshat's first small monthly Pink Sheet exercise in the recent sequence. Future Seshat work should complement, not duplicate, Gold Lab v2.

Cycle 169 also issued first-month forecasts on the 2nd/6th day **after the target month began**. That is causal under its conservative data gate, but not a forecast issued before the quarter began. Cycle 170 tests a *strictly pre-quarter* cutoff, using a PDF snapshot two quarterly batches earlier; horizons rise from 1–3 to 4–6 months. Errors between protocols are **not** comparable as same-horizon model skill.

| Protocol; 18 monthly targets Apr 2025–Sep 2026 | Persistence MAE (USD/toz) | Linear3 MAE |
|---|---:|---:|
| Cycle 169 late issue | 327.06 | 269.89 |
| Cycle 170 pre-quarter issue | 662.17 | 512.78 |

### Instability hidden by pooled cycle 169 average
| Late-issue subset | Persistence MAE | Linear3 MAE |
|---|---:|---:|
| Apr–Dec 2025 (9 months) | 302.67 | **107.78** |
| Jan–Sep 2026 (9 months) | **351.44** | 432.00 |

Linear3's advantage **reversed sign** in 2026. These are retrospective inspected subsets, not held-out prospective results. For strict pre-quarter forecasts, the exhaustive six-batch cluster-bootstrap 95% percentile interval for persistence-minus-Linear3 MAE was **[-118.94, +475.44] USD/toz**. Only six dependent quarterly clusters: no formal coverage guarantee or robust edge claim.

## Provenance and verification
- Original 24 rounded monthly gold USD/toz observations, Oct 2024–Sep 2026, were inherited from the cycle 169 local attachment. Not all rows were independently reverified this cycle.
- Independently spot-checked against official dated World Bank PDFs: Apr/May/Jun 2025 = 3218/3309/3353 in July 2, 2025 PDF; Jul/Aug/Sep 2026 = 4073/4411/4319 in October 2, 2026 PDF.
- Gold Lab `SOURCES.md` records a source-definition change around June 2025 from the World Bank workbook Description sheet (London PM fixing average to spot average). This was *not independently reverified from workbook* this cycle; comparisons spanning the boundary deserve caution.
- The PDF issue date is a **conservative availability certificate**, not necessarily the first public release of each price. Monthly averages are not executable trading quotes.
- Local command: `python -m unittest -q test_cycle169 test_cycle170` → **18/18 passed**. Verified strict dates, horizons, same targets, future-label mutation invariance, metric reproduction, source spot-checks.
- Full code, 24-row ledger, tests, output JSON, checksums: conversation attachment `seshat_cycle170_prequarter_regime_audit.zip`. The compact self-contained reproduction script is stored alongside this report.

## Next experiment
Audit existing Gold Lab v2 *prospective* receipts for immutability, code/issue timestamps, provider vintage and settlement integrity; avoid retuning on inspected 2025–26 prices. Do not change peer state or promote production models based on these exploratory results.

Primary World Bank PDFs:
- https://thedocs.worldbank.org/en/doc/18675f1d1639c7a34d463f59263ba0a2-0050012025/related/CMO-Pink-Sheet-July-2025.pdf
- https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Pink-Sheet-October-2026.pdf
