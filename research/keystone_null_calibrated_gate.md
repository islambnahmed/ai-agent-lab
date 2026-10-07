# Keystone: null-calibrated sequential gate

## Question
Can the evidence-budget router keep its changed-regime value while explicitly controlling false switches under the no-change regime?

## Experiment
Seeded Monte Carlo, 20,000 runs/cell, Bernoulli baseline p0=0.9, 100 evaluation observations, representative decision costs C=4 and safe cost s=1. Slow estimate alpha=0.03; fast estimate alpha=0.3.

Replace the prior point-KL horizon trigger with a sequential generalized likelihood-ratio (GLR) gate for a downward change. At each time t, compute the Bernoulli log likelihood ratio between p0 and the constrained running MLE qhat <= p0. The fast path is unlocked only after cumulative GLR >= h. Before that, decisions use the slow estimate.

This is a falsification prototype, not a claim of exact anytime-valid type-I control: repeated GLR thresholding needs stronger calibration for a formal guarantee.

## Results
Mean cumulative decision regret; false-switch rate is probability the fast path is ever unlocked under q=0.9.

| h | q=.9 regret | false switch | q=.7 | q=.5 | q=.3 | q=.1 |
|---|---:|---:|---:|---:|---:|---:|
| 4 | 0.270 | 2.97% | 11.16 | 18.83 | 8.31 | 3.87 |
| 5 | 0.076 | 0.815% | 11.93 | 20.93 | 11.09 | 6.93 |
| 6 | 0.035 | 0.350% | 12.44 | 22.24 | 11.90 | 7.10 |
| 7 | 0.028 | 0.180% | 12.90 | 23.97 | 14.32 | 10.06 |
| 8 | 0.016 | 0.055% | 13.10 | 24.99 | 15.38 | 10.33 |

For context, the prior point-KL router had q=.9 regret 7.511 and changed-regime regrets q=.7 11.930, q=.3 8.920, q=.1 8.200 in the same qualitative task family.

## Interpretation
The no-change failure is not inherent to routing. A persistence/evidence gate can reduce null regret by roughly two orders of magnitude while retaining useful changed-regime behavior. But the threshold creates a real safety/responsiveness frontier: stronger null protection delays unlocking the fast path and can materially increase regret after true changes.

The surprising result is that h=4 is already close to the old router on q=.7 and q=.3, dramatically better on q=.1, while reducing the null failure from ~7.5 regret to ~0.27. At h=5, false switches fall below 1% but some changed-regime performance is sacrificed.

## Design correction
Do not use a fixed evidence-horizon threshold as the router's primary gate. Separate:
1. action relevance / value of switching;
2. sequential evidence that a regime change is persistent;
3. a tunable false-switch budget.

The next architecture should choose the evidence threshold from decision cost, not a universal h. High-cost false switches warrant a larger h; high-cost delayed reaction warrants a smaller h.

## Next falsification
Derive/test a cost-aware threshold rule and compare it with fixed h over the earlier phase diagram, including no-change probability. Also replace raw repeated GLR with an anytime-valid e-process or explicitly calibrated boundary before making statistical guarantees.
