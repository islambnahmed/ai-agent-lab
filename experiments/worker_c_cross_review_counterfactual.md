# Worker C cycle — Cross-review as counterfactual routing evidence

## Question
Can outcomes already produced by peer review/cross-evaluation replace protected random exploration when learning which agent fits a task context?

## Reversible simulation
Four task contexts and four agents. Each context has one specialist with success probability 0.82; non-specialists have 0.55. Baseline is contextual Thompson sampling using only the selected agent's observed outcome. Experimental router additionally receives a binary pseudo-outcome for each unselected agent from a simulated cross-review channel.

20 independent seeds, T=1500 for the reviewer-accuracy sweep.

| reviewer accuracy q | selected-only regret | cross-review regret |
|---|---:|---:|
| 0.50 | 50.73 | 94.89 |
| 0.55 | 56.66 | 87.84 |
| 0.60 | 53.70 | 48.74 |
| 0.65 | 45.24 | 40.05 |
| 0.70 | 48.51 | 33.49 |
| 0.75 | 50.09 | 23.58 |
| 0.80 | 48.09 | 19.66 |
| 0.90 | 52.18 | 16.36 |
| 1.00 | 57.51 | 11.61 |

The crossover in this setup is around q≈0.60. At q=0.80, cross-review reduced mean regret by ~59% relative to the selected-only baseline in this sweep.

## Counterexample: systematic reviewer preference
A second test kept q=0.80 but gave pseudo-reviews a systematic false-positive preference for agent 0. With 30 seeds:
- no preference: selected-only 52.50 vs cross-review 19.27
- false-positive boost 0.50: 51.11 vs 50.87 (benefit essentially erased)
- false-positive boost 0.70: 55.88 vs 106.69 (cross-review becomes much worse)

## Working-model change
Cross-review can be valuable counterfactual evidence and can avoid paying a permanent random-exploration tax, but only if its calibration is independently trustworthy. More feedback is not automatically better: correlated/systematic evaluator bias can dominate the routing learner.

Therefore raw peer scores should NOT be fed directly into routing state. The reusable architecture is a **calibrated counterfactual channel**:
1. selected-agent outcomes remain ground truth;
2. peer/cross-review evidence is tracked separately by reviewer and task context;
3. pseudo-evidence receives weight only after calibration against later observable ground truth;
4. disagreement/correlation between reviewers is itself evidence, not independent votes.

## Transfer target
Next test should use real lab artifacts where multiple agents evaluated the same claim/test, measuring reviewer calibration and dependence before allowing cross-review to influence routing. Synthetic results alone do not establish real-agent reliability.
