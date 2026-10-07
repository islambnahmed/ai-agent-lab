# Keystone: information limit for regime detection

## Why this test
Recent tuning showed that uncertainty penalties and faster EWMA adaptation do not solve weak regime changes. Before adding more detector machinery, quantify how much statistical evidence the observations can contain.

## Benchmark
For Bernoulli old regime p0=0.9 and true new regime q, the expected oracle log-likelihood evidence per post-change observation is the Bernoulli KL divergence:

D(q || p0) = q log(q/p0) + (1-q) log((1-q)/(1-p0)).

Using a nominal false-alarm evidence scale log(1/0.02)=log(50)=3.912, an optimistic first-order sample benchmark is:

n_info ~= log(50) / D(q || 0.9).

This is not claimed as an exact finite-horizon lower bound for the current detector; it is an information-rate benchmark. It is favorable to the detector because it assumes the alternative q is already known.

## Results
| New q | KL nats/obs | optimistic n_info |
|---|---:|---:|
| 0.10 | 1.7578 | 2.23 |
| 0.20 | 1.3627 | 2.87 |
| 0.30 | 1.0326 | 3.79 |
| 0.50 | 0.5108 | 7.66 |
| 0.70 | 0.1537 | 25.46 |
| 0.80 | 0.0444 | 88.10 |

## Interpretation
The weak-change slowdown is largely information-limited, not just a tuning defect. Moving from 0.9 to 0.7 supplies about 11.4x less KL evidence per observation than moving from 0.9 to 0.1. A 0.9 -> 0.8 shift supplies about 39.6x less.

This explains why attempts to make the fast memory more plastic can backfire: rapid adaptation can erase the mismatch before enough cumulative evidence exists, while no score transformation can manufacture missing information.

The previously observed ~38-observation delay for 0.9 -> 0.7 is therefore better interpreted against an optimistic known-alternative information scale of ~25.5 observations, rather than against the ~5-observation performance on large shifts.

## Design consequence
Stop optimizing one detector for all shift sizes. Treat adaptation as two regimes:
1. **Fast change response** for high-information shifts, where sequential prequential evidence can react quickly.
2. **Slow drift tracking** for low-information shifts, where forcing an early binary alarm is statistically expensive and may be the wrong objective.

A useful next experiment is to compare predictive regret of continuous slow adaptation versus alarm-and-reset behavior across weak shifts (0.9 -> 0.8/0.7), under the same false-alarm budget. If slow tracking wins, Keystone should separate 'change detection' from 'drift adaptation' instead of trying to make one mechanism do both.
