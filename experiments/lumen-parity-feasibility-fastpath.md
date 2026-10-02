# Lumen audit: parity fast path for deterministic binary constraints

## Question

Experiment 29 proves that edgewise-consistent Bernoulli pairwise marginals on a forest are globally realizable. What useful structure survives when the graph contains cycles?

## Deterministic edge subclass

Suppose binary variables `X_v in {0,1}` are connected by deterministic pairwise constraints

`X_v = X_u XOR b_uv`, where `b_uv in {0,1}`.

- `b=0`: equality edge.
- `b=1`: inequality / perfect-anticorrelation edge.

For an edge with Bernoulli marginal `p_u=P(X_u=1)`, consistency forces

- equality: `p_v=p_u`;
- inequality: `p_v=1-p_u`.

These are stronger than merely passing edgewise Frechet bounds.

## Theorem

A connected deterministic-constraint graph is globally feasible iff the XOR of edge labels around every cycle is zero, and the supplied node marginals obey the propagated equality/complement relations.

### Necessity

XOR all edge equations around a cycle. Every node variable occurs twice and cancels, leaving

`0 = XOR b_e`.

Thus every cycle must contain an even number of inequality edges.

### Sufficiency

Choose a root `r`. For each vertex define `q_v` as the XOR of edge labels along any path from `r` to `v`. The zero-XOR cycle condition makes `q_v` path-independent.

Set

`X_v = Z XOR q_v`

for one Bernoulli root variable `Z`. Then every edge constraint holds identically. Choose `P(Z=1)=p_r`; the node-marginal propagation conditions give all requested marginals.

So this subclass does not require a global LP even on cyclic graphs.

## Algorithmic consequence

Use disjoint-set union with parity (weighted Union-Find):

1. Store for each node its XOR parity to the component representative.
2. Adding constraint `X_v XOR X_u = b` either merges two components or checks an already-implied parity.
3. A contradictory cycle is detected exactly when an in-component edge disagrees with the implied parity.
4. Separately check node marginal compatibility under the inferred parity.

With path compression and union by rank, a batch of constraints costs `O((V+E) alpha(V))`, effectively linear.

## Regression cases

- Triangle, all three edges inequality: infeasible (cycle XOR = 1).
- Four-cycle, all four edges inequality: feasible.
- Triangle with two inequality edges and one equality edge: feasible.
- Any tree: cycle test is vacuous, recovering the deterministic special case of Experiment 29.

## Boundary of the result

This is a fast path, not a replacement for general marginal feasibility. Non-deterministic pairwise tables on cyclic graphs can still require a global feasibility method. A cycle by itself is neither proof of infeasibility nor proof that LP is necessary.

## Implementation recommendation

Before invoking a generic global oracle, classify exact deterministic binary edges. If an entire connected component is deterministic, solve it with parity DSU and marginal propagation. Send only genuinely non-deterministic cyclic components to the expensive global solver.

This converts the odd-cycle counterexample into a reusable algorithmic capability rather than only a warning case.
