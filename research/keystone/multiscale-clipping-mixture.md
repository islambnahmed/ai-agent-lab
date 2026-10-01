# Keystone — Multiscale clipping without post-hoc threshold selection

## Motivation

The sharp second-moment bridge gives, for Y_B = clip(X,-B,B),

```
|E[X] - E[Y_B]| <= M2/(4B)
```

when E[X^2] <= M2. A single B is therefore a bias/concentration tradeoff. Choosing B after seeing outcomes would reintroduce selection/look-ahead risk.

## Safe construction

Predeclare thresholds B_j and nonnegative weights w_j with sum_j w_j = 1. For each j, build an e-process E_{j,t} that is valid for the original mean null after applying the corresponding bias allowance M2/(4 B_j).

Then

```
E_mix,t = sum_j w_j E_{j,t}
```

is itself an e-process, because conditional expectation is linear:

```
E[E_mix,t | F_{t-1}]
  = sum_j w_j E[E_{j,t} | F_{t-1}]
 <= sum_j w_j E_{j,t-1}
  = E_mix,t-1.
```

Thus Ville's inequality gives

```
P_0(sup_t E_mix,t >= 1/alpha) <= alpha.
```

This adapts across effect scales without choosing a threshold after observing the current data.

## Exact price relative to an oracle component

Suppose component j is the one an oracle would have chosen. Since

```
E_mix,t >= w_j E_{j,t},
```

a sufficient condition for the mixture to reject is

```
E_{j,t} >= 1/(alpha w_j).
```

The oracle component alone only needs E_{j,t} >= 1/alpha. Therefore the mixture pays an additive log-evidence penalty

```
log(1/w_j).
```

This is the key quantity to benchmark, not merely the number of thresholds.

For J equally weighted scales, the worst-case penalty is log J. A geometric prior over increasingly extreme scales gives unequal penalties: common scales can be cheap while remote scales pay more.

If log E_{j,t} grows at asymptotic rate g_j > 0 under an alternative, the corresponding first-order delay overhead is approximately

```
Delta t_j ~= log(1/w_j) / g_j.
```

So multiscale adaptation is not free, but its cost is explicit and often only logarithmic in the number of candidate scales.

## Design implication

A useful grid should be geometric in B (or equivalently in target effect size), not dense and linear. Nearby thresholds have highly redundant behavior; adding many near-duplicates increases the mixture penalty without buying much scale coverage.

Under the earlier Hoeffding-style balance for target effect Delta,

```
B*(Delta) = M2/(2 Delta),
```

a geometric effect grid Delta_j = Delta_0 r^j induces a geometric clipping grid B_j = B_0 r^{-j}. This covers orders of magnitude with O(log range) components.

## Important limitation

The mixture proof requires each component to be valid under the same declared null/assumption set. Mixing cannot repair an invalid component model, an unjustified M2 bound, or a threshold/scoring rule that used the current outcome before commitment.

Also, the inequality E_mix >= w_j E_j gives a sufficient detection condition, not an equality for stopping times: other components may help the mixture cross earlier.

## Next experiment

Benchmark geometric multiscale mixtures against an oracle B that knows the alternative effect size in advance. Report:
1. type-I crossing rate under matched second-moment nulls;
2. median/quantile detection delay across effect sizes;
3. observed delay regret versus the oracle;
4. predicted log(1/w_j)/g_j overhead versus measured overhead;
5. sensitivity to grid ratio r and prior weights.

This directly tests whether safe adaptation buys enough robustness to justify its explicit oracle penalty.
