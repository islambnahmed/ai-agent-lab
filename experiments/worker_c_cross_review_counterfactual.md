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


## Follow-up: calibration is not enough when reviewer errors are dependent

A paired synthetic test weighted pseudo-evidence by each reviewer's online measured accuracy above chance. In 12 seeds (T=1200), this reduced mean regret from 51.03 to 34.61 for weak q=.58 reviewers and from 63.88 to 49.10 under a systematic positive preference. But with a shared-error mechanism, raw and calibrated regret were essentially tied (31.59 vs 32.00).

A second counterexample used two reviewers per candidate with shared errors. Naively treating their reviews as additive evidence was compared with a conservative rule: agreeing reviews receive at most 0.6 total pseudo-observation and disagreement receives zero. In 16 paired seeds (T=1500):
- shared-error 0.00: naive 19.12, capped 19.93
- 0.15: 29.31 vs 27.20
- 0.30: 63.48 vs 47.22
- 0.45: 205.94 vs 118.33

This changes the working model: reviewer accuracy and reviewer dependence are separate quantities. Accuracy calibration cannot protect against a shared blind spot when reviewers fail together. Real routing should require both calibration against objective outcomes and error-overlap/dependence estimates; correlated agreement must have an evidence cap rather than being counted as independent votes.

These are synthetic small-sample results and are not evidence that real lab reviewers have these calibration levels. The transfer target is objective-test-backed lab artifacts where reviewer error overlap can be measured.
