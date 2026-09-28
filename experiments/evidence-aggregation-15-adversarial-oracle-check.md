# Evidence Aggregation 15 — Adversarial Oracle Check

## Goal
Attack the small-n dependence-bounds oracle itself rather than adding another dependence example.

## Checks performed
1. Analytical two-event Frechet check over the 11 x 11 grid a,b in {0.0,0.1,...,1.0}. For every one of 121 cases, the oracle matched:
   - lower P(A and B) = max(0, a+b-1)
   - upper P(A and B) = min(a,b)
2. Feasible-distribution property test. Using deterministic seed 0, generate 500 random probability distributions over the eight binary worlds for three failure modes. Derive marginals and all three pairwise moments from each generated distribution, query the oracle, and check that the generating distribution's P(all fail) lies inside the returned interval.
3. Infeasible-constraint sanity check: marginals 0.1,0.1 with pairwise intersection 0.2 must be rejected.

## Result
- Frechet mismatches: 0 / 121.
- Feasible generating distributions outside returned bounds: 0 / 500.
- The impossible intersection case was rejected.

This is stronger evidence than Experiment 14 because the oracle was tested against an independent analytical identity and hundreds of feasible joint distributions rather than one hand-selected case.

## Remaining attack surface
The prototype still uses tiny-system vertex enumeration and floating-point Gaussian elimination. Passing these checks does not establish numerical robustness near degenerate or nearly dependent constraints.

Next high-value attack: construct epsilon-scale near-degenerate feasible and infeasible cases around the solver tolerances, then decide whether to harden the prototype or replace its numerical core with a solver-backed implementation.
