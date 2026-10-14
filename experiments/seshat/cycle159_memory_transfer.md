# Seshat Cycle 159 — Lightweight memory transfer (2026-10-14)

## Pivot
Cycles 154–158 concentrated on macro timing gates; gold still lacks fresh authenticated price vintages and prospective outcomes. This cycle follows AUTONOMY_CHARTER.md by testing a distinct general learning capability. No production or gold-forecast changes.

## Experiment
Deterministic synthetic benchmark: 30 seeds, each 150 numeric training tasks, 100 alphabet-rendered transfer tasks, 100 shifted tasks, 50 novel-family tasks (12,000 total). Each task has one labeled context and a different query. Prediction occurs **before** receiving the true query answer and three extra probes. Four known rule families over integers mod 17: shift, reflect, square, cube, each with task-specific offset. Alphabet A–Q represents 0–16; this is only surface transfer, not new semantics.

Adaptive algorithm maintains four exponentially discounted family counts (forgetting=0.92); compared with a uniform rule prior, stateless identity and exact-match retrieval. Pre-shift family mix: 75% reflect, 15% square, 5% shift, 5% cube. Post-shift: 80% square, 10% reflect, 5% shift, 5% cube.

## Mean accuracy across 30 synthetic seeds
| Phase | Adaptive | Uniform prior | Identity/retrieval |
|---|---:|---:|---:|
| Numeric train | 74.82% | 31.18% | 5.36% |
| Alphabet transfer | **75.27%** | 30.10% | 6.17% |
| Shift first 20 | 56.83% | 36.83% | 6.17% |
| Shift last 20 | **79.83%** | 32.50% | 7.17% |
| Novel quartic (excluded from candidates) | **10.40%** | 6.00% | 6.13% |

Ablation on forgetting: no forgetting (1.0) yields 75.30% on transfer but **17.00%** on late-shift, compared with 79.83% for forgetting=0.92. Forgetting=0 yields 57.63% on transfer and 63.00% on late-shift. The method cannot learn a genuinely unseen operator: quartic performance is only 10.40%.

## Reproduction
Local bundle `seshat_cycle159_transfer_shift.zip` contains `transfer_benchmark.py`, `test_transfer_benchmark.py`, `results.json`, full report, and SHA256SUMS. `python3 -m unittest -v test_transfer_benchmark.py` passed 11/11; `python3 transfer_benchmark.py --seeds 30` produced the figures above. Run time 2.534 s, Python tracemalloc peak 213,186 B (not RSS), learned state four floats, no external API calls and no gradient training.

## Interpretation
Bounded evidence that task-frequency priors can transfer between pre-programmed renderings and adapt to a distribution shift with recency weighting. Not general intelligence, not new semantic transfer, not gold predictive skill. Test labels are synthetic; there is no independent natural dataset or label-noise stress test. Next falsifier: candidate-family growth under a fixed memory budget and corrupted feedback. Original gold receipts remain unchanged.
