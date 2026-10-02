# Lumen: parity feasibility executable regression

## Goal
Turn the deterministic binary same/opposite feasibility result into an executable, dependency-free regression oracle.

## Algorithm
Maintain a disjoint-set forest. For every node, `xor_to_parent` stores its XOR relation to its parent. An edge constraint `x_u XOR x_v = r` is feasible iff:
- different components can be merged while preserving the requested parity;
- nodes already in one component have implied parity equal to `r`.

This detects every inconsistent parity cycle, not merely odd cycles. Complexity is effectively linear: `O((V+E) alpha(V))`.

## Marginals
For Bernoulli marginals `p_i=P(X_i=1)`, a parity constraint implies:
- parity 0 (same): `p_v=p_u`
- parity 1 (opposite): `p_v=1-p_u`

The executable oracle below tests structural parity first, then exact/tolerance-aware marginal compatibility. This is deliberately a fast path only for deterministic XOR constraints; general probabilistic pairwise constraints still require a global feasibility method.

## Regression cases
1. triangle with three opposite edges -> infeasible
2. four-cycle with four opposite edges -> feasible
3. triangle with two opposite + one same -> feasible
4. triangle with one opposite + two same -> infeasible
5. structurally feasible edge with incompatible marginals -> infeasible

The fourth case is important: "odd cycle" is only shorthand for the all-opposite special case. The general invariant is XOR parity around every cycle equals zero.
