# Keystone — Clipping bias envelope under a second-moment assumption

## Goal
Repair the estimand shift exposed by Khepri Experiment 38 without pretending clipping is lossless.

Let
```
Y = clip(X, -B, B)
```
for `B > 0`.

The exact pointwise distortion is
```
|X - Y| = (|X| - B)_+.
```
Therefore
```
|E[X] - E[Y]| <= E[(|X| - B)_+].
```

If the original variable satisfies the explicit assumption
```
E[X^2] <= M2,
```
then for every real `x`,
```
(|x|-B)_+ <= x^2/(4B).
```
The constant 1/4 is sharp: for `u=|x|/B >= 1`,
`(u-1)/u^2` is maximized at `u=2`, with value `1/4`.

Hence the sharper distribution-free bridge is
```
|E[X] - E[clip(X,-B,B)]| <= M2/(4B).
```

A looser but simpler bound `M2/B` also follows from
`(|x|-B)_+ <= |x| 1{|x|>B} <= x^2/B`, but it wastes a factor of four.

## Consequence for testing the original mean
Suppose the scientific null is `E[X] <= mu0`. Under the second-moment assumption,
```
E[Y] <= mu0 + M2/(4B).
```
So a bounded-data sequential test may be applied to `Y` against the shifted null
`mu0 + M2/(4B)`. This preserves inference about the original mean, at the cost of
an explicit bias allowance.

This is not free robustness:
- small `B` gives tighter bounded observations but a larger bias allowance;
- large `B` reduces clipping bias but weakens bounded-data concentration.

Thus `B` is a bias-versus-concentration tuning parameter, not merely an outlier cutoff.

## Boundary of the result
Without a tail/moment assumption, clipping cannot generally be transferred back to the
original mean with a finite universal correction. Arbitrarily rare, arbitrarily large
values can preserve the clipped distribution while changing `E[X]` by an arbitrary amount.

## Reproducible checks
The sharp inequality can be checked after scaling `B=1`:
- `u=2`: left side `1`, right side `u^2/4 = 1` (equality);
- `u=1`: left side `0`, right side `1/4`;
- `u=10`: left side `9`, right side `25`.

## Next experiment
Compare, under the same declared second-moment assumption:
1. a global hard-bound e-process;
2. clipping plus the valid `M2/(4B)` bias envelope;
3. a heavy-tail sequential method designed directly for finite variance.

Measure both type-I control and detection delay. This avoids comparing methods under
different hidden assumptions.
