# Experiment 29 — Constructive forest feasibility theorem

## Question

When marginal Bernoulli probabilities and selected pairwise joint probabilities are supplied, when is local Fréchet feasibility sufficient for a globally valid joint distribution?

## Result

If the graph whose vertices are Bernoulli variables and whose edges are the supplied pairwise constraints is a **forest**, then local Fréchet feasibility on every edge is sufficient for global feasibility.

A cycle is therefore not evidence of infeasibility. It is the point at which edge-local checks cease to be a complete certificate and a global feasibility test may be needed.

## Constructive proof

For one tree component, choose an arbitrary root. Give the root its specified Bernoulli marginal. For every directed parent-child edge (u,v), let p_u=P(X_u=1), p_v=P(X_v=1), and q=P(X_u=1,X_v=1).

When 0<p_u<1 define

- P(X_v=1 | X_u=1) = q/p_u
- P(X_v=1 | X_u=0) = (p_v-q)/(1-p_u)

The Fréchet inequalities max(0,p_u+p_v-1) <= q <= min(p_u,p_v) imply both conditional probabilities lie in [0,1].

Boundary cases are also well-defined:

- p_u=0 forces q=0; choose P(X_v=1|X_u=0)=p_v.
- p_u=1 forces q=p_v; choose P(X_v=1|X_u=1)=p_v.

Now sample the root, then recursively sample each child from its conditional distribution given its parent. Because a tree gives each non-root vertex exactly one parent, these local conditionals cannot conflict. Each child obtains marginal p_v and every constrained edge obtains joint q exactly.

For a forest, construct each tree component this way and combine components independently. This yields a global joint distribution satisfying all supplied marginals and pairwise constraints.

## Engineering consequence

A future n-variable dependence-bounds implementation can use graph structure as a certified fast path:

1. Validate each supplied edge against exact Fréchet bounds.
2. If the constraint graph is a forest, feasibility is already proven; do not invoke an expensive global-feasibility check merely to validate the inputs.
3. If the graph contains a cycle, do **not** reject it. Instead, local checks are inconclusive and a global LP/feasibility method is required.

This refines the earlier informal claim that cycles "trigger inconsistency": cycles trigger the **need to check**, not inconsistency itself.

## Status

Analytic proof. No implementation change is claimed here.
