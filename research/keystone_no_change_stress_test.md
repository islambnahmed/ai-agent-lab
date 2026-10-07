# Keystone: no-change stress test exposes router failure mode

## Why this test
The prior decision-cost phase diagram omitted q=0.9 (no regime change). That omission can hide the cost of transient fast-estimator noise. Before tuning or claiming routing value, test the null regime.

## Protocol
Independent seeded Monte Carlo reproduction of the prior Bernoulli decision task, 30,000 runs per reported cell, 100 baseline + 100 evaluation observations. Baseline p=0.9. Representative costs C=4, safe cost s=1. Policies use the same qualitative definitions as the phase-diagram checkpoint: alarm-only, slow EWMA alpha=0.03, and fixed evidence-horizon router using fast EWMA alpha=0.3 with horizon log(50)/KL(fast||0.9) <= 20.

Reported values are mean cumulative action regret; parenthetical values are Monte Carlo standard errors.

## Result
- no change q=0.9: alarm 0.102 (0.099), adapt -0.060 (0.100), router **7.511 (0.113)**
- q=0.7: alarm 15.720 (0.105), adapt 11.208 (0.088), router 11.930 (0.094)
- q=0.3: alarm 18.049 (0.072), adapt 18.473 (0.056), router 8.920 (0.078)
- q=0.1: alarm 14.632 (0.069), adapt 19.166 (0.054), router 8.200 (0.078)

The tiny negative adapt regret under q=0.9 is Monte Carlo noise around zero, not a real advantage.

## Major correction
The fixed evidence-horizon router has a serious null-regime failure: fast-estimator fluctuations can make KL from baseline temporarily large, so the router treats noise as actionable evidence and switches behavior even though nothing changed. Its ~7.5 regret under no change is many standard errors from zero.

Therefore the prior result “router wins a plurality of changed-regime cells” is insufficient evidence of a generally useful architecture. The no-change case is not a minor missing benchmark; it changes the design requirement.

## Design consequence
Do **not** route merely because a point estimate implies a short evidence horizon. A viable router needs two gates:
1. **decision relevance** — would plausible regime uncertainty change the action?
2. **sequential evidence / persistence** — is there calibrated evidence that the deviation is real rather than a noisy fast estimate?

This suggests replacing the current point-KL trigger with a cost-aware sequential gate (e.g. confidence/e-value or persistence-controlled evidence) and evaluating changed and unchanged regimes jointly.

## Next falsification
Construct a null-calibrated router with an explicit false-switch budget, then compare total decision regret across q={0.9,0.7,0.5,0.3,0.1}. Require confidence intervals and report false-switch frequency under q=0.9. If the null-calibrated router loses most of the changed-regime advantage, retire the routing architecture rather than tune around the result.

This checkpoint corrects the interpretation of the prior phase diagram; it does not erase the earlier result.
