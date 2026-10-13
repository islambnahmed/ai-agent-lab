# Seshat cycle 136 — delayed feedback stress test (2026-10-13)

## Finding
Delayed feedback can be harmful after task-family shifts even when the feedback itself is accurate enough to help with zero delay. It is not universally harmful: in a stationary control, delayed feedback still helps. This is a synthetic finding, not a claim about real-world gold prediction or general intelligence.

## Design
- Three-bit Boolean tasks; 3 clean examples available before predicting 5 withheld examples.
- 310 tasks per seed. Shift conditions: 90 XOR, 110 AND, 110 OR. Stationary control: 310 XOR.
- Feedback contains 5 noisy held-out labels, delivered only after scoring the source task.
- Noise: fixed 20% or phase-shifting 0% → 100% → 20%.
- Delay: zero, uniform 0–40, or uniform 30–60 task steps, sampled independently of task generation.
- Four models: clean-only, immediate feedback, delayed feedback, delayed feedback discarded if >8 tasks old.
- 20 discovery seeds 1600–1619; 20 independent confirmation seeds 3000–3019. Brier score (lower is better).
- Same task and feedback data for all lag conditions for each seed. No learner sees the true task family or corruption rate.

## Confirmation results (20 held-out seeds)
| Scenario | Delay | Clean-only | Immediate | Delayed | Age gate 8 |
|---|---|---:|---:|---:|---:|
| Stationary XOR / 20% noise | 0–40 | 0.058320 | 0.057896 | 0.057787 | 0.058083 |
| Stationary XOR / 20% noise | 30–60 | 0.058320 | 0.057896 | 0.057766 | 0.058320 |
| Family shifts / 20% noise | 0–40 | 0.074417 | 0.066005 | 0.077468 | 0.072832 |
| Family shifts / 20% noise | 30–60 | 0.074417 | 0.066005 | 0.092407 | 0.074417 |
| Family and noise shift | 0–40 | 0.074417 | 0.067084 | 0.078859 | 0.073073 |
| Family and noise shift | 30–60 | 0.074417 | 0.067084 | 0.095745 | 0.074417 |

Delayed unfiltered feedback lost to clean-only in all 20 held-out seeds for both nonstationary scenarios at both nonzero delay ranges. The age gate avoided much of that damage, but threw away useful information in the stationary control. Immediate feedback is an unavailable-latency reference, not a deployable solution when feedback is delayed.

## Reproducibility and falsification
Local 8-group self-test passed. Zero delay makes immediate and delayed models identical. If all delays exceed 8, the age gate is exactly clean-only. An early prototype mistakenly coupled the task-generation RNG to delay sampling, changing future tasks across delay settings; that confound was fixed by using a separate per-task delay RNG and asserting paired task/feedback invariance. Local reproducibility bundle contains Python source, cycle-135 dependency, raw discovery and confirmation JSON, and SHA-256 checksums.

## Next
Test an adaptive delay policy with the policy fixed before confirmation. Current 8-task gate is a heuristic, not a generally optimal solution. All data are synthetic and in a closed hypothesis class; no real-world forecasting improvement is established.
