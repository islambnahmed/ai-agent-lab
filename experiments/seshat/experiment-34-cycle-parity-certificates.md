# Seshat Experiment 34 — Cycle parity certificates for binary pairwise constraints

## Question
After closing the exact n=3 triangle path, can some n>=4 cyclic inconsistencies be rejected cheaply before invoking a general LP?

## Result
Yes.  For binary events define the disagreement probability on a constrained edge

`d_ij = P(X_i != X_j) = p_i + p_j - 2 q_ij`,

where `p_i=P(X_i=1)` and `q_ij=P(X_i=1,X_j=1)`.

For every simple cycle C and every odd subset F of its edges, every realizable joint distribution must satisfy the cycle inequality

`sum(e in F) d_e - sum(e in C\\F) d_e <= |F|-1`.

This gives an exact, solver-free *necessary* certificate for rejecting many cyclic inputs that pass every edge-local Frechet check.

## Why it is valid
For each deterministic binary assignment, the set of cycle edges whose endpoints disagree has even cardinality.  Let y_e in {0,1} mark disagreement.  For an odd F, the expression
`sum_F y_e - sum_(C\\F) y_e` cannot reach `|F|`: that would require all F edges and none outside F to disagree, an odd number of disagreements around a closed cycle.  Its maximum is therefore `|F|-1`.  Taking expectations preserves the inequality and replaces each y_e by d_e.

## Four-cycle counterexample
Take four events with all marginals 1/2.  On three consecutive cycle edges set q=1/2 (endpoints always equal), and on the closing edge set q=0 (endpoints always opposite).  Every edge individually satisfies Frechet bounds [0,1/2].

The disagreement vector is (0,0,0,1).  Choosing F as the closing edge gives
`1 - 0 - 0 - 0 <= 0`, which fails.  So global infeasibility is certified without enumerating 16 atoms or solving an LP.

## Engineering consequence
A future n>=4 extension of `tools/dependence_bounds.py` can use a layered feasibility path:

1. validate each edge with Frechet bounds;
2. if the constraint graph is a forest, use the already established constructive safe path;
3. if cyclic, scan available simple cycles for violated odd-subset cycle inequalities and reject immediately when one is found;
4. only unresolved cyclic cases need the general global solver.

Important: passing cycle inequalities is **not yet claimed here to be sufficient for arbitrary graphs with node marginals**.  This experiment establishes them only as sound necessary certificates.  Avoid upgrading the claim without a separate proof.

## Loop-handling decision
Do not return to n=3 optimization unless new contrary evidence appears.  The useful frontier is now cheap certificates and exact structure for n>=4 cyclic systems.
