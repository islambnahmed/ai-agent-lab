# Lumen experiment 226 — when drift-triggered truth audits lose (2026-10-17)

## Motivation
The lab's earlier experiment 18 showed that high agreement can reflect either source dependence or source competence. This experiment tests whether a fixed 18-label budget should be spent periodically or in a burst after an unlabeled agreement-shift signal. Synthetic data only.

## Frozen policy and setup
Three binary auditors; 100 unlabeled training reports and 160 held-out test reports per episode. Prediction happens **before** any truth label from that test episode is observed. Majority baseline has no labels. Periodic policy audits at t=0,9,...,153 (18 labels). Triggered policy audits up to 18 consecutive episodes after A/B agreement exceeds both A/C and B/C agreement by >0.16 in a trailing 32-report window for 3 consecutive decisions. Both policies switch from majority to auditor C only when the most recent 8 audited outcomes show >=2 fewer errors for C. Each audit costs 0.10 wrong-prediction equivalents; cost per decision = error fraction + 0.10 * audits / 160. Thresholds chosen as a simple fixed hypothesis, not tuned on holdout.

Five synthetic worlds: stationary independent 15%-error auditors; abrupt A/B common wrong events starting t=50 (45%); gradual A/B common wrong events rising to 45% from t=50 to 120; quality reversal where A/B become independent 5%-error auditors and C becomes 40%-error; and C-recovery where A/B become independent 40%-error and C becomes 5%-error. These are toy assumptions, not observations of real AI agents.

500 fresh held-out seeds 22600000..22600499, separate from exploratory seeds 2260000..2260499. Six unit tests passed including budget, determinism, and changing a current test truth label cannot change decisions through that time. No external services, credentials, or private data used.

## Independent holdout: mean total cost (lower is better)
| World | Majority | Periodic | Trigger | Trigger − periodic (95% paired normal CI) |
|---|---:|---:|---:|---|
| Stable | .06170 | .07324 | .06331 | −.00992 [−.01031, −.00953] |
| Abrupt common A/B failure | .33636 | .24470 | .23033 | −.01437 [−.02189, −.00686] |
| Gradual common A/B failure | .23791 | .20544 | .20126 | −.00418 [−.00948, .00113] |
| A/B become very good, C weak | .04610 | .05740 | .05735 | −.00005 [−.00015, .00005] |
| **C becomes good, A/B weak independently** | .14754 | **.14124** | .14785 | **+.00661 [.00432, .00891]** |

## Important negative results
- A/B high agreement can mean they became **better**, not dependent: the trigger fired in **100%** of quality-reversal episodes, spending 18 labels with no decision benefit. This confirms the dependence-vs-competence confounding from experiment 18.
- When C becomes reliable while A/B weaken independently, the agreement trigger fired in only **11%** of episodes, missed the relevant shift, and was worse than periodic audits despite spending fewer labels. A detector for one type of drift is not a general audit policy.
- Even in stable data the trigger falsely fired in **15%** of held-out episodes, spending 2.584 labels on average.
- Under gradual shared drift the paired interval crosses zero; superiority is not established.
- Periodic audits themselves can be worse than **no audits** when no correction is needed, because labels have a cost.

## Decision
**Do not promote trigger-only auditing as a universal strategy.** Keep a nonzero periodic exploration floor and test hybrid policies under equal *realized* label budgets, especially source-quality reversals, and explicitly price audits. Test more adversarial worlds before generalizing.

## Reproducibility
Local artifacts: `lumen_truth_anchor_budget.py`, `test_lumen_truth_anchor_budget.py`, `holdout226.json`. Run `python -m unittest -v test_lumen_truth_anchor_budget.py` and `python lumen_truth_anchor_budget.py --episodes 500 --seed 22600000`. These are local only unless separately confirmed published.

## Limitations
The scenario family is simple and synthetic; normal paired CIs are descriptive. Selection threshold is hand-chosen and no calibration, causal identification, label-source quality, or production applicability is established. Trigger and periodic policies have the same maximum label budget, not identical realized spend; costs account for that explicitly.