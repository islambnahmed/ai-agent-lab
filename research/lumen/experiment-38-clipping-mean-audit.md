# Lumen audit — Experiment 38 clipping mean

## Claim checked

Khepri Experiment 38 states that, for the asymmetric mean-zero construction

- X = 10 with probability p
- X = -10p/(1-p) otherwise,

clipping X to [-1,1] gives a transformed mean "approximately -9p".

That description is locally correct but can be made exact, and its domain matters.

## Exact derivation

For 0 <= p <= 1/11, the negative support point satisfies

10p/(1-p) <= 1.

So only the positive value is clipped. The transformed variable Y = clip(X,-1,1) is

- Y = 1 with probability p
- Y = -10p/(1-p) with probability 1-p.

Therefore

E[Y] = p - (1-p) * 10p/(1-p) = -9p.

Thus the values used in Experiment 38 are exact:

- p = 0.005 -> E[Y] = -0.045
- p = 0.01 -> E[Y] = -0.09.

At p = 1/11 both formulas meet at -9/11.

For p > 1/11, the negative support point is also outside [-1,1], so clipping maps the two outcomes to +1 and -1. Then

E[Y] = p - (1-p) = 2p - 1.

Hence the full transformed mean is piecewise:

E[clip(X,-1,1)] =
- -9p, for 0 <= p <= 1/11
- 2p - 1, for 1/11 < p <= 1.

## Why this matters

The substantive lesson of Experiment 38 is unchanged: clipping can restore a bounded-input guarantee while changing the estimand. The audit sharpens that lesson: transformation bias should be derived over the parameter domain rather than extrapolated from a local approximation.

This is also a useful guardrail for future robustification experiments: when a transformation has thresholds, derive its estimand distortion piecewise before interpreting simulation results.
