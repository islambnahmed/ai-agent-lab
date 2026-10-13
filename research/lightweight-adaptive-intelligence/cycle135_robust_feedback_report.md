# Seshat cycle 135 — latent feedback reliability (2026-10-13)

## Why this experiment
Cycle 134 showed that learning from more feedback can **harm** a small adaptive learner when labels are corrupted. This cycle tests a falsifiable alternative: jointly infer the task-family prior and a latent feedback-error rate rather than trusting all labels.

## Experimental protocol
- **Synthetic only**: 3-bit Boolean tasks; 18 hypotheses across XOR, AND, OR, input pairs and output inversion.
- Family phases: 100 XOR tasks, then 200 AND, then 200 OR. Three **clean** labels are visible on each task; five hidden labels are scored **before** revealing `q=0,1,5` feedback labels.
- The old baseline assumes a fixed 15% label-error likelihood on all labels. A **clean-only** ablation learns from the three clean labels but ignores feedback. The new learner treats the clean labels as exact, marginalizes across compatible hypotheses and feedback error rates `{0,0.2,0.5,1.0}`, and updates its three family probabilities and four reliability probabilities **only after scoring**.
- No learner is told the true family or actual noise rate. Uniform and frozen controls use the same task stream across conditions; feedback RNG is separate.
- Family EMA rate = 0.12, reliability EMA rate = 0.15, family prior floor = 0.02. These were fixed before the independent confirmation seeds.
- Discovery: eight seeds 1400–1407. Independent confirmation: four seeds 3000–3003. Metric: Brier loss (lower better).

## Confirmation results (4 independent seeds; q=5)
| Corruption | AND old | AND clean-only | AND robust | OR old | OR clean-only | OR robust |
|---|---:|---:|---:|---:|---:|---:|
| 0% | .064336 | .065480 | **.063338** | .061252 | .064018 | **.060933** |
| 20% | .067223 | .065480 | **.064090** | .066037 | .064018 | **.061870** |
| 50% | .111491 | .065480 | **.065457** | .123772 | .064018 | **.064017** |
| 100% flipped | .239791 | .065480 | **.063338** | .232952 | .064018 | **.060933** |
| 35% off-grid | .076570 | .065480 | **.065094** | .079941 | .064018 | **.063477** |
| 75% off-grid | .219915 | .065480 | **.065238** | .232724 | .064018 | **.063287** |
| Noise phases 0/50/100% | .120574 | **.065480** | .065649 | .244213 | .064018 | **.063453** |

Under fully flipped feedback, robust AND loss .063338 vs old .239791 and robust OR loss .060933 vs old .232952. At 50% random corruption, robust essentially matches clean-only rather than degrading sharply. This is not a universal win: under abrupt noise changes, AND robust (.065649) is slightly worse than clean-only (.065480).

The learner's final inferred noise averaged 0.200003 at true 20%, 0.499023 at true 50%, and 1.0 at true 100%. At off-grid 75% noise it inferred only ~0.6042, showing calibration limits.

## Reproducibility and limitations
- A local Python stdlib-only script was tested with 12 checks: posterior normalization, no current-task leakage, paired controls, determinism, no noise learning when q=0, clean-only ablation, and shifted corruption.
- **This is synthetic evidence only**, not gold-price prediction, general intelligence, or a production-ready reliability estimator.
- The noise grid contains the main experimental rates, including 100% inversion; results may weaken under adversarial non-iid errors, larger task classes, wrong assumptions about the three clean labels, or less informative feedback.
- Discovery and confirmation sets are small; no confidence interval or significance claim. The old baseline treats clean labels as noisy, which contributes to the gap; the clean-only ablation isolates the value of feedback modeling.
- No claim that tests ran in GitHub CI. A source bundle is retained locally in the cycle artifact.

## Decision
Retain the joint latent-noise hypothesis as a promising **research** direction, not a deployed system. Next falsification: adversarially targeted errors, mislabelled 'clean' examples, delayed feedback, and online noise-regime shifts. Compare against clean-only, not only the weak fixed-noise baseline.
