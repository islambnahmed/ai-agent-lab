# Worker A cycle 266 — volatility-change detector trade-off (2026-10-21)

## Purpose
Challenge the cycle265 false-negative problem instead of endlessly tuning the warning latch. All experiments are offline and synthetic; no trading or production integration.

## Reproducible design
- Deterministic seeded Gaussian log returns, 40 seeds (1000–1039) per scenario, 500 closes each; change at close index 320.
- Four causal methods: **legacy** (3-return, 1.2% floor, 5x baseline, severe 6% jump), **ratio8** (8-return median, 60-return non-overlapping baseline, 3x ratio, 0.3% recent and 0.2% absolute median increase), **ratio5** (5-return median, 3.5x ratio, same floors), and **hybrid** (legacy OR ratio8).
- Early detection is any alert during closes 320–334. False-alarm rates count individual origin alarms, not distinct warning episodes. No tuning was performed against the 40-seed results, but methods were designed after observing earlier synthetic failures; this is exploratory, not an independent gold-market holdout.

| Scenario (40 seeds) | Legacy early detections | Ratio8 | Ratio5 | Hybrid |
| --- | ---: | ---: | ---: | ---: |
| Volatility 0.15% -> 0.60% (4x) | 2 | 36 | 38 | 36 |
| Volatility 0.20% -> 0.50% (2.5x) | 1 | 30 | 29 | 30 |
| Volatility 0.30% -> 0.45% (1.5x) | 0 | 3 | 6 | 3 |
| Alternating +/-0.7% after baseline | 0 | 40 | 40 | 40 |
| One-time +8% outlier | 40 | 0 | 1 | 40 |

Stationary control false-alert origins per 1,000 checks:
- 0.1% volatility: all methods 0 / 17,000.
- 0.4% volatility: legacy 1/17,000, ratio8 11/17,000, ratio5 11/17,000, hybrid 12/17,000.
- 1.2% volatility: legacy 3/17,000, ratio8 11/17,000, ratio5 11/17,000, hybrid 14/17,000.

## Conclusion
**The fixed absolute floor creates material misses.** Ratio-based median detectors substantially improve moderate-shift sensitivity on this constructed family, but can miss a single extreme jump and generate more false alarms. A hybrid catches both in this benchmark, but incurs the union of false alerts. Even ratio detectors miss most 1.5x shifts within 15 closes. The single-outlier alert can itself be a bad tick; a warning must not be interpreted as proof of a real regime change.

## Caveats and next decision
These observations are **not** evidence of gold forecast skill, calibrated coverage, production readiness, or real-world false-positive frequency. Simulated origins are dependent and seeds are not necessarily representative. Thresholds are exploratory. The prototype latch's release receipt remains unauthenticated and should not be wired to a forecast UI. Next: separate data-quality spikes from genuine volatility shifts, evaluate false-alert **episodes** and alert duration, and then test on a chronologically held-out authorized gold dataset with point-in-time provenance.

No main-branch changes. Benchmarks are intended to be reproduced using the accompanying standalone script, with local tests covering invalid inputs, insufficient history, causal prefix behavior and synthetic step detection.
