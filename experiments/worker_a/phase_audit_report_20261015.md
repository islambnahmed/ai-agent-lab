# Worker A — Phase sensitivity audit, 2026-10-15

Read the committed Standard Bullion readiness and HistData research reports. Reconstructed coverage from every disjoint offset phase: all six horizon groups match their published totals. Seven deterministic audit checks passed.

| Source | Horizon | Overall coverage | Per-phase coverage | Samples per phase |
|---|---:|---:|---:|---:|
| Standard Bullion | 1 | 90.77% | 90.77% | 65 |
| Standard Bullion | 7 | 77.97% | 50–87.5% | 8–9 |
| Standard Bullion | 30 | 88.89% | 0–100% | 1–2 |
| HistData | 1 | 64.81% | 64.81% | 645 |
| HistData | 7 | 63.85% | 56.04–70.33% | 91–92 |
| HistData | 30 | 68.67% | 57.14–80.95% | 20–21 |

Standard Bullion h30 has 32 of 36 overlapping windows covered, but each disjoint offset has only 1–2 observations; four offsets have zero covered and 26 have all covered. Do not infer reliable 30-close predictive coverage from this sparse retrospective audit. Different providers are not directly comparable. No prospective outcome or raw provider snapshot was authenticated. No production changes.

Run: `node experiments/worker_a/phase_audit.mjs products/gold-forecast/reports/readiness-20261012.json products/gold-forecast/reports/research-benchmark-20261012.json`.
