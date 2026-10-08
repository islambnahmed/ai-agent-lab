# Keystone — Fixed-capital e-process insurance (2026-10-08)

## Decision
**Do not replace either the uniform or the quadratic adaptive detector with a 50/50 mixture.** A fixed convex mixture is mathematically valid under the same calibration assumptions but creates a measurable sensitivity tradeoff; it does not dominate both components.

## Research question
Can a valid mixture of the existing uniform and evidence-weighted transition e-processes retain the uniform detector's strength on p01 increases and the adaptive detector's strength on p11 changes?

## Method
- Fixed, pre-data capital split: E_mix(t)=lambda E_uniform(t)+(1-lambda) E_adaptive_quadratic(t), lambda in {0,.25,.5,.75,1}.
- 400 time steps, change after 120, 4,000 paths/scenario, 16 independently calibrated groups of 250; calibration 2,000 Bernoulli observations per transition row.
- Markov null p01=1/36, p11=.75; transition alternatives p01 up .12, p11 up .90, p11 down .20, both up, and a marginal-preserving change.
- Alarm when E_mix >= 25 (alpha=.04). Simulated calibration uses Clopper-Pearson row intervals with total nominal failure <=.01.
- All methods see the *same simulated paths*, making the comparison paired.

## Main simulation results (alarm probability, 4,000 paths each)
| Scenario | adaptive only (lambda=0) | 50/50 | uniform only (lambda=1) |
|---|---:|---:|---:|
| stable | .0003 | .0010 | .0010 |
| p01 increase | .6252 | .6790 | .7133 |
| p11 increase | .1195 | .1105 | .0948 |
| p11 decrease | .1278 | .1168 | .0958 |
| both increase | .7995 | .8185 | .8210 |
| marginal-preserving switch | .0245 | .0220 | .0182 |
| predictable in-interval null | .0003 | .0005 | .0008 |

**Independent random-seed replication** (4,000 new paths/scenario, fresh calibration): p01 up .6910/.7395/.7662; p11 up .1075/.0970/.0823; p11 down .1232/.1118/.0965; both up .8173/.8303/.8363; marginal-preserving .0270/.0230/.0200 (adaptive/50-50/uniform). Same tradeoff direction.

## Mathematical verification
For fixed lambda selected before observations, a convex combination of nonnegative supermartingales is a nonnegative supermartingale. Under the null and covered calibration intervals, Ville's inequality gives P(ever E_mix >=1/alpha) <= alpha. Including possible calibration noncoverage gives <= alpha+delta = .05. **These guarantees do not apply outside the conditional row-probability intervals or with post-hoc lambda selection.**

An exhaustive path check across 3 Markov null kernels, 381 histories and 5 weights verified nonpositive one-step conditional supermartingale excess (floating point tolerance 1e-10).

## Limitation and next move
No uniform improvement was found: mixing redistributes sensitivity. The low p11 detection rates remain a bottleneck. Next high-value experiment: test a channel-specific predictable allocation that directly boosts rare-row exposure, with preregistered scenarios and fresh held-out calibration; avoid tuning against the same test scenarios.

## Reproducibility
Local files created and run: `keystone_mixture_insurance.py` and `keystone_mixture_insurance_results.json` (not included in this GitHub commit unless separately uploaded). Seed 202610082239; holdout seed 1701/1702. This report distinguishes committed summary from local code/results.
