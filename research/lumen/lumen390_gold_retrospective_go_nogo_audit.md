# Lumen 390 — Gold Lab: retrospective decision audit (no prospective promotion)

**Date:** 2026-10-24. **Repository:** `islambnahmed/ai-agent-lab`. **Worker branch:** `sandbox/worker-c`.
**Decision:** Do not promote a predictive model or assert a trading edge from the available evidence. Keep persistence as the default comparison and require independently verified prospective outcomes before any promotion.

## Method and reproducibility

Read two *already committed derived reports* from `main` (no raw provider history was downloaded, modified, or redistributed). These are **different provider measurements and date ranges**, so their rows and performance metrics are **not pooled**.

- Standard Bullion irregular daily XAU closes, 324 observations, 2025-10-12–2026-10-11: [readiness report](https://github.com/islambnahmed/ai-agent-lab/blob/main/products/gold-forecast/reports/readiness-20261012.json), Git blob SHA `740b51e96120f11b3737b72173d80d9f7b13a4bf`, generated 2026-10-12T17:12:52.101Z.
- HistData XAUUSD minute **bid** prices aggregated to UTC observed closes, 3221 observations, 2016-01-03–2026-05-31: [research benchmark](https://github.com/islambnahmed/ai-agent-lab/blob/main/products/gold-forecast/reports/research-benchmark-20261012.json), Git blob SHA `93912b6dc5c3ba5f215730edfce698cfaa82efba`, generated 2026-10-12T18:18:34.512Z.
- Predeclared benchmark target: nominal **80%** interval coverage; comparison baseline: **persistence** ([benchmark contract](https://github.com/islambnahmed/ai-agent-lab/blob/main/products/gold-forecast/benchmark.json)).

For each horizon below, `hits = round(reported_coverage_percent × reported_audit_n / 100)`; percentage-point gap = reported coverage − 80. MAE is in USD per troy ounce. The hit counts are **reconstructed from rounded aggregate coverage**, not independently recomputed from withheld raw price rows.

## Longer research series: calibration warning

| Horizon (future observed closes) | Frozen selected model | Reconstructed covered / n | Reported coverage | Gap vs 80% | Model MAE | Persistence MAE | MAE skill vs persistence |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 418/645 | 64.81% | -15.19 pp | 31.70 | 31.70 | 0.00% |
| 7 | persistence | 408/639 | 63.85% | -16.15 pp | 88.84 | 88.84 | 0.00% |
| 30 | persistence | 423/616 | 68.67% | -11.33 pp | 183.97 | 183.97 | 0.00% |

**Finding:** All three nominal 80% intervals under-covered in the long retrospective audit by 15.19–16.15 percentage points for h1/h7 and 11.33 pp for h30. The selected model is persistence at every horizon, hence *zero* model-vs-persistence MAE improvement by construction. This is a descriptive calibration shortfall, **not** a formal independent-trial significance test; h7/h30 forecast windows overlap, and even h1 can have serial dependence. The report uses inspected, current-vintage history rather than point-in-time immutable historical vintages.

## More recent Standard Bullion series: no selected-model advantage

| Horizon (future observed closes) | Frozen selected model | Reconstructed covered / n | Reported coverage | Gap vs 80% | Model MAE | Persistence MAE | MAE skill vs persistence |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | persistence | 59/65 | 90.77% | 10.77 pp | 39.41 | 39.41 | 0.00% |
| 7 | mean_reversion | 46/59 | 77.97% | -2.03 pp | 122.52 | 118.88 | -3.06% |
| 30 | momentum | 32/36 | 88.89% | 8.89 pp | 258.77 | 226.33 | -14.33% |

The h7 selected mean-reversion model has -3.06% retrospective MAE skill vs persistence; h30 selected momentum has -14.33%. The h1 selection **is** persistence, so 0% improvement is tautological. Short-horizon interval coverage differs from the HistData report because the provider, measurement, sample length, and audit dates differ. The recent h30 coverage estimate is based on only 36 overlapping observations; do not read it as a verified 80% coverage guarantee.

## Macro Ridge: inspected ablation, not a candidate for automatic promotion

| Horizon | Eligible audit n | Macro Ridge MAE skill vs persistence | Macro Ridge MAE skill vs price-only Ridge | Nonoverlapping phase n |
|---|---:|---:|---:|---:|
| 1 | 642 | -2.37% | -1.07% | 642 |
| 7 | 636 | -8.52% | -9.89% | 92 |
| 30 | 613 | 7.66% | -6.48% | 21 |

A positive h30 macro-vs-persistence result (7.66%) coexists with a negative h30 macro-vs-price-only result (-6.48%). Moreover, its disjoint phase has only 21 cases. This is **inspected retrospective analysis** with incomplete macro release-time vintages, not a clean forward experiment.

## Operational decision and next falsifiable step

1. **Do not promote** any gold predictor, change the frozen selector, or claim prospective forecast skill. The verified structural screening tests from Lumen 389 do not authenticate source evidence.
2. **Keep distinct scorecards** for Standard Bullion observed closes and HistData UTC bid closes. No cross-provider target substitutions; no extrapolation from one to the other.
3. Before evaluating a new prospective receipt, independently verify its committed bytes/anchor time, original provider vintage and prefix, exact future observed-close sequence, and first-publication chronology. A self-reported `true` verification flag is not independent proof.
4. When verified future outcomes exist, compute paired absolute errors against persistence on the **same** origins and the empirical interval coverage; report counts, provider definition, and overlap/dependence. Require a sufficiently large fresh sample and an explicit promotion rule set **before** inspecting its outcomes.

**No live gold prices, fresh vendor outcomes, independently authenticated target vintages, or forward skill were established this cycle.** This audit changes neither code nor security settings. All actions stayed within the authorized repository.
