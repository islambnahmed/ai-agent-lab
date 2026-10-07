# Keystone: evidence-budget routing

## Result

The information-limit calculation suggests a routing rule rather than another detector tweak.

For Bernoulli baseline p0=0.9 and a 2% evidence target, use the optimistic evidence horizon

```
N_min(q) = log(1/0.02) / KL(Bern(q) || Bern(0.9))
```

This reproduces the earlier scale:
- q=0.1: ~2.23 observations
- q=0.5: ~7.66 observations
- q=0.7: ~25.46 observations
- q=0.8: ~88.10 observations

## Architectural consequence

Do not force one mechanism to both alarm on abrupt changes and chase weak drift.

Use an **evidence budget**:
1. Maintain prequential estimates of plausible alternative regimes.
2. Estimate the information rate against the long-term model.
3. Convert that rate into an optimistic evidence horizon.
4. If the horizon is short enough for the application's reaction budget, route to fast change detection.
5. If the horizon is too long, do not manufacture confidence by tuning thresholds; route to slow adaptation and continue accumulating evidence.

This turns the previous qualitative split ("fast change" vs "slow drift") into a measurable routing criterion.

## Falsifiable next test

Compare three policies under equal false-alarm budget and compute:
- predictive regret,
- detection delay for abrupt shifts,
- adaptation regret for gradual drift,
- unnecessary reset count.

Policies:
A. alarm-only detector;
B. slow-adaptation-only learner;
C. evidence-budget router.

The router is useful only if C lowers combined regret without hiding meaningful abrupt changes.

## Caution

N_min is an optimistic information scale, not a guaranteed finite-sample stopping time. It assumes the alternative q is known; an online learner pays additional estimation cost.
