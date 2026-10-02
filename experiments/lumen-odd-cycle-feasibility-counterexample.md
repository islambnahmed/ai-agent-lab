# Lumen — Odd-cycle counterexample for pairwise Bernoulli feasibility

## Question

Experiment 29 proves that edgewise Frechet feasibility is sufficient when the constraint graph is a forest. What is the smallest concrete example showing why a cycle needs a genuinely global check?

## Triangle counterexample

Take three Bernoulli variables X1, X2, X3 with

- P(Xi=1)=1/2 for every i;
- P(Xi=1,Xj=1)=0 on all three edges of the triangle.

Each edge passes its exact Frechet bounds:

max(0, 1/2+1/2-1)=0 <= q=0 <= 1/2.

For a pair with both marginals 1/2 and q=0, the only possible pair law puts probability 1/2 on (1,0) and 1/2 on (0,1). Hence every constrained edge requires its endpoints to differ almost surely.

The first two edges imply X1 != X2 and X2 != X3, so X1=X3 almost surely. The third edge requires X1 != X3 almost surely. Contradiction. Therefore every local edge is feasible while no global joint distribution exists.

## Generalization

The same construction works on any odd cycle: assign marginal 1/2 to every vertex and perfect anticorrelation to every edge. Alternating 0/1 values around an odd cycle cannot return consistently to the starting vertex.

This is not a claim that cycles are generally infeasible. Even cycles admit the alternating construction, and many cyclic constraint sets are globally feasible.

## Regression-test consequence

A future global-feasibility implementation should include at least these paired tests:

1. triangle / odd-cycle perfect anticorrelation: local Frechet checks pass, global feasibility must fail;
2. four-cycle perfect anticorrelation: local checks pass and global feasibility must succeed.

Together they guard against both mistakes: treating local checks as globally sufficient on cycles, and treating the mere presence of a cycle as evidence of inconsistency.

## Status

Analytic counterexample and regression-test specification. No solver implementation is claimed here.
