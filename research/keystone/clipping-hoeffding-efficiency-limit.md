# Keystone — A hidden cost of clipping under only a second-moment bound

## Question

The previous multiscale construction safely adapts over clipping thresholds. But is the underlying clipped-Hoeffding component itself statistically efficient when the only assumption is

```
E[X^2] <= M2
```

and the target alternative has mean gap `Delta > 0`?

## Worst-case growth calculation

For `Y_B = clip(X,-B,B)`, the sharp bridge proved earlier gives

```
E[Y_B] - mu0 >= Delta - M2/(4B).
```

Call the guaranteed residual signal

```
s(B) = Delta - M2/(4B).
```

A Hoeffding e-factor for a variable in `[-B,B]` has log-growth lower-bound surrogate

```
g(B, lambda) = lambda s(B) - lambda^2 B^2/2.
```

Optimizing over `lambda` gives

```
lambda*(B) = s(B)/B^2
g*(B) = s(B)^2/(2 B^2).
```

Now optimize over B. Writing z = 1/B,

```
g*(z) = 0.5 z^2 (Delta - M2 z/4)^2.
```

The interior maximizer is

```
z* = 2 Delta/M2
B* = M2/(2 Delta),
```

which recovers the threshold derived previously. At this point,

```
s(B*) = Delta/2
g_oracle = Delta^4/(2 M2^2).
```

Therefore accumulating log evidence `L` requires, at this worst-case-growth scale,

```
n ~ L/g_oracle
  = 2 M2^2 L / Delta^4.
```

## Important consequence

The clipping + worst-case bias + Hoeffding route has a `Delta^-4` evidence-time scaling in this conservative analysis.

That is a warning sign. Finite-variance mean estimation/testing can often attain the familiar `Delta^-2` scale with robust variance-aware methods. So the multiscale mixture solves the *threshold-selection* problem, but it does not solve the more important *statistical efficiency* problem of this component family.

The mixture penalty `log(1/w_j)` may be small while the base component is still orders of magnitude slower than a better heavy-tail construction.

## Why this happens

Two costs compound:

1. To keep clipping bias below a constant fraction of Delta, the threshold must grow like `B = Theta(M2/Delta)`.
2. Hoeffding pays concentration cost proportional to `B^2`.

Combining them turns a residual signal of order Delta into growth of order

```
Delta^2 / B^2 = Theta(Delta^4/M2^2).
```

This is not a defect in the multiscale mixture proof. It is a consequence of pairing a worst-case clipping-bias bridge with range-based Hoeffding concentration.

## Revised research priority

Do not spend the next cycles only tuning the geometric grid. First benchmark a variance-aware heavy-tail e-process / robust mean construction under the same second-moment assumption.

The decisive comparison should be:

- validity under the identical assumption set;
- log-growth or detection delay versus Delta;
- empirical scaling as Delta shrinks;
- whether the variance-aware method approaches `Delta^-2` while clipped-Hoeffding follows the conservative `Delta^-4` regime;
- only then measure the extra adaptation cost from unknown scale.

## Falsification target

The `Delta^-4` statement above is a conservative growth guarantee derived from the sharp bias envelope plus Hoeffding. It is not yet a minimax lower bound on every clipped procedure, nor a claim that every distribution realizes equality simultaneously in every bound.

A useful next experiment should deliberately search for distributions near the second-moment extremizers and determine how tight the predicted scaling is. If empirical clipped-Hoeffding behavior is substantially better, separate “guaranteed worst-case rate” from “typical rate” rather than conflating them.
