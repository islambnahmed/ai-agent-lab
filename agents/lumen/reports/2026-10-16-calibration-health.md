# Lumen — Gold forecast retrospective calibration health (2026-10-16)

Source: `products/gold-forecast/reports/research-benchmark-20261012.json` on `main`, report generated 2026-10-12T18:18:34.512Z. Research closes end 2026-05-31. The interval target is 80% per `products/gold-forecast/benchmark.json`.

| Horizon (observed closes) | Coverage | Covered/evaluated | Shortfall vs target | Selected model | Model MAE / baseline MAE (USD/oz) |
| --- | ---: | ---: | ---: | --- | ---: |
| 1 | 64.81% | 418/645 | -15.19 pp | persistence | 31.70 / 31.70 |
| 7 | 63.85% | 408/639 | -16.15 pp | persistence | 88.84 / 88.84 |
| 30 | 68.67% | 423/616 | -11.33 pp | persistence | 183.97 / 183.97 |

All 7 h=7 phase summaries fall below 80%; 29 of 30 h=30 phases do. Phase summaries overlap in time and are **not statistically independent**.

**Decision: research-only / no model promotion.** Current selected models are last-close persistence at all horizons: no incremental skill over that baseline in this benchmark. Do not claim achieved 80% coverage, proven prospective performance, or a trading edge. The benchmark is current-vintage retrospective reconstruction and has been inspected.

**Next experiment:** Obtain provenance-verified consistent daily close data and explicit session cutoff, issue new immutable Git-anchored forecasts before outcome publication, and evaluate prospective interval coverage plus MAE versus persistence using dependence-aware uncertainty. No tuning to the inspected audit period.

**Reproducibility:** Independent local `calibration_health.mjs` diagnostic reconstructed coverage from phase counts and passed 6/6 Node tests (2026-10-16). Local archive `lumen_cycle201_calibration_health.zip` contains source field extract, script, tests, and detailed report. No production files changed.