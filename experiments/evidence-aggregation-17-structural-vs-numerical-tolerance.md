# Evidence Aggregation 17 — Structural vs Numerical Tolerance

## Trigger
A second adversarial pass found that Experiment 16 still allowed a mathematically impossible pairwise joint when the contradiction was smaller than `FEAS_TOL`.

Example:
- P(A) = 0.1
- P(B) = 0.1
- P(A and B) = 0.1 + 5e-13

The joint exceeds its exact upper Frechet bound, even though the excess is below the solver feasibility tolerance.

## Change
Commit `185ff341cb3183ea0b722d06e7607bc886dfc2fb` separates two concepts:
- **structural input validity**: supplied pairwise probabilities must satisfy Frechet bounds with direct comparisons;
- **numerical feasibility**: `FEAS_TOL` remains internal to floating-point vertex solving.

A regression test now checks both the earlier 1e-9 contradiction and the new 5e-13 contradiction.

## Result
The known sub-tolerance input-validation hole is closed at the API boundary. This is narrower than proving the floating-point solver robust: feasible cases close to singular bases remain an open attack surface.

## Next attack
Build an exact rational reference for n<=3 and differential-test float bounds near degenerate vertices, focusing on false infeasibility and bound drift rather than re-testing Frechet validation.
