# Khepri 323 — Feedback Counterfactual Audit (2026-10-20)

**Synthetic research only; no production changes.** This audit challenges Exp322's interpretation of GARCH shock-detection power. The complete executable reproduction is available in the local experiment bundle `khepri_exp323_reproducible.zip`; code is not claimed to be in this branch unless independently verified.

## Paired experiment
Held Exp322's two threshold sets fixed. For each of 600 fresh seeds per case, generated (a) original OOD GARCH with injected shocks feeding into conditional variance and (b) an intervention with identical innovations, shock times and magnitudes but no propagation of injected shocks into future variance. Gaussian and Student-t3 GARCH were both tested. Evaluated the *first alarm after change with no earlier alarm*, not any later alarm. Nine unit tests passed.

## Results: recalibrated OOD thresholds, first-post alarm / 600
| Family | Change | Feedback | No feedback |
|---|---|---:|---:|
| Gaussian GARCH | single 20-unit spike | 469 (78.17%) | 19 (3.17%) |
| Student-t3 GARCH | single 20-unit spike | 374 (62.33%) | 6 (1.00%) |
| Gaussian GARCH | rare jumps | 526 (87.67%) | 25 (4.17%) |
| Student-t3 GARCH | rare jumps | 545 (90.83%) | 33 (5.50%) |
| Gaussian GARCH | post-change 3x scaling | 595 (99.17%) | 269 (44.83%) |
| Student-t3 GARCH | post-change 3x scaling | 594 (99.00%) | 160 (26.67%) |

## Major correction: the '3x' feedback generator is explosive
Exp322 feeds `x_t = 3 sqrt(h_t) z_t` back into `h_(t+1) = (1-a-b) + a x_t^2 + b h_t` with `a=.16, b=.81`. For unit-variance innovations, the expected variance multiplier is `b + 9a = 2.25 > 1` (versus `b+a=.97<1` under null). It is *not* a stationary 3x volatility regime. Across 600 episodes per family, the median last-20 / first-20 post-change RMS ratio was 11,244,579.62 for Gaussian feedback and 31,072.80 for Student-t3 feedback, versus 0.9934 and 0.9715 for no feedback. All 600 feedback episodes in each family exceeded 10x; none of the no-feedback episodes did.

## Decision
The hybrid detects shock *propagation* far more readily than truly isolated spikes. Exp322's near-perfect 3x detection must not be presented as performance on stationary 3x volatility. Separate and pre-register isolated jump, volatility cascade, and stationary scale-shift cases. No live-gold claims. The result is a generator/evaluation correction, not evidence of a production bug.

## Reproduction
Bundle files: `feedback_counterfactual.py`, `test_feedback_counterfactual.py`, `results323.json`, `README_323.md`, Exp322 and Exp321 dependencies. Commands: `python -m unittest -v test_feedback_counterfactual.py`; `python feedback_counterfactual.py --episodes 600 --output results323.json`.
