# Keystone: first evidence-budget router stress test

## Purpose
Test the falsifiable next step from evidence-budget routing: does a simple Detect-vs-Adapt router reduce predictive regret versus alarm-only behavior without sacrificing abrupt-shift detection?

## Protocol
Seeded Monte Carlo, 10,000 runs per condition, Bernoulli baseline p=0.9, change begins at t=100, horizon 200.

Policies:
- **alarm**: frozen long model + prequential EWMA detector (alpha=0.3, h=6); reset long model to fast estimate on alarm.
- **adapt**: slow EWMA predictor (alpha=0.03), no alarm.
- **router**: same detector, but predictions use fast EWMA when the estimated KL evidence horizon log(50)/KL(fast||long) <= 20 observations; otherwise slow EWMA.

Abrupt alternatives q in {0.1,0.5,0.7}; gradual conditions linearly drift from 0.9 to q over t=100..199.

Metric: cumulative log-loss regret against an oracle that knows the true Bernoulli probability. Alarm statistics use first alarm.

## Results
| shift | policy | regret | false alarm | detection | mean delay |
|---|---|---:|---:|---:|---:|
| abrupt 0.9→0.1 | alarm | 30.42 | 2.21% | 97.79% | 5.73 |
| | adapt | 27.34 | — | — | — |
| | router | 29.30 | 2.21% | 97.79% | 5.73 |
| abrupt 0.9→0.5 | alarm | 22.12 | 2.21% | 97.29% | 18.37 |
| | adapt | 8.37 | — | — | — |
| | router | 11.98 | 2.21% | 97.29% | 18.37 |
| abrupt 0.9→0.7 | alarm | 20.65 | 2.21% | 63.40% | 40.18 |
| | adapt | 3.78 | — | — | — |
| | router | 9.26 | 2.21% | 63.40% | 40.18 |
| gradual 0.9→0.1 | alarm | 23.40 | 2.21% | 97.79% | 46.98 |
| | adapt | 10.61 | — | — | — |
| | router | 13.08 | 2.21% | 97.79% | 46.98 |
| gradual 0.9→0.5 | alarm | 18.31 | 2.21% | 82.00% | 68.03 |
| | adapt | 4.23 | — | — | — |
| | router | 8.33 | 2.21% | 82.00% | 68.03 |
| gradual 0.9→0.7 | alarm | 11.94 | 2.21% | 30.77% | 70.68 |
| | adapt | 2.42 | — | — | — |
| | router | 6.79 | 2.21% | 30.77% | 70.68 |

## Interpretation
The first router is **not yet a win**. It consistently reduces predictive regret relative to alarm-only while preserving that detector's alarm behavior, but slow adaptation alone has lower predictive regret in every tested condition.

This exposes a missing objective: prediction regret alone rewards quiet adaptation and gives no value to explicit regime identification/reset. A router can only be justified when alarms have downstream value (e.g. selecting a different policy/model, protecting against catastrophic action, or preserving interpretable regime memory) that exceeds their reset/false-alarm cost.

## Durable lesson
Do not optimize the router against log-loss alone and then claim an architectural advantage. The next benchmark must include an action-dependent cost where delayed recognition of a large shift is genuinely expensive, alongside false-alarm/reset cost. Otherwise adapt-only is the correct simple baseline.

## Next test
Define a minimal decision task with asymmetric action loss and compare alarm, adapt, and router under matched false-alarm cost. Sweep reaction-budget cutoff rather than tuning it on one regime.
