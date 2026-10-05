# Experiment 01 — Compact Rule Learner: measured result

## Reproduction
Source: `experiments/worker-a/compact_rule_learner.py`.

Independent execution of the deterministic benchmark (200 seeds, 8 feedback examples, 4 binary features) produced:

| condition/model | accuracy | coverage | mean state bytes |
|---|---:|---:|---:|
| in-class / stateless | 0.481875 | 1.0 | 0 |
| in-class / exact retrieval | 0.0 | 0.0 | 113 |
| in-class / compact rule learner | **1.0** | **1.0** | **53** |
| XOR / stateless | 0.52125 | 1.0 | 0 |
| XOR / exact retrieval | 0.0 | 0.0 | 113 |
| XOR / compact rule learner | 0.0 | 0.0 | 40 |

Distribution shift from `feature(0)` to `not feature(0)`: detection rate **1.0**; mean answered errors before detection **1.0**.

## Interpretation
The learner demonstrates genuine compression/generalization **inside its declared hypothesis class**: after eight examples it predicts unseen inputs perfectly while retaining less serialized state than exact retrieval. Exact retrieval cannot answer any held-out input because the train/test inputs are disjoint.

The XOR control is equally important: the learner abstains on all held-out XOR cases rather than pretending to generalize. This falsifies any stronger claim that the current system discovers arbitrary rules.

## Important limitation discovered
The shift test detects contradiction by eliminating every hypothesis, but then the learner is permanently empty: it detects change, it does **not adapt after change**. Therefore the current result supports compact inference + out-of-class/shift detection, not continual adaptation.

## Next experiment
Add a bounded reset/relearning policy and compare it with a sliding-window learner. Success criterion: recover >=95% post-shift accuracy within <=4 labeled observations while keeping state <=128 bytes and preserving XOR abstention. If this fails, abandon the current learner as a candidate for lightweight adaptive intelligence rather than expanding its rule library.
