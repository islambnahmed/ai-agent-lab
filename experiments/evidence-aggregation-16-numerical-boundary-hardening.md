# Evidence Aggregation 16 — Numerical Boundary Hardening

## Trigger
Adversarial review found inconsistent tolerances in `tools/dependence_bounds.py`: negative basic variables were accepted to 1e-9 while residuals were accepted to 1e-8. A mathematically impossible pairwise constraint only 1e-9 above its marginal could therefore risk being blurred by feasibility tolerances.

## Counterexample
For binary failures A and B:

- P(A) = 0.1
- P(B) = 0.1
- P(A and B) = 0.100000001

This is impossible because P(A and B) <= min(P(A), P(B)) = 0.1.

## Change
Commit `1538720a545827de437fb0a815cfdf4073c7636a`:
- uses one strict `FEAS_TOL = 1e-12` for non-negativity and equality residual checks;
- validates every supplied pairwise joint against its necessary Frechet bounds before vertex enumeration;
- adds the near-boundary contradiction as a regression test.

## Result
The previously identified tolerance gap is removed by construction for pairwise constraints. This does **not** prove full numerical robustness: ill-conditioned equality systems and larger future n remain separate attack surfaces.

## Next attack
Construct feasible and infeasible cases within a few ulps of Frechet boundaries and compare float results with an exact rational oracle for n<=3.