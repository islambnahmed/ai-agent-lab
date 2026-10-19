# Keystone — independent forest-bounds LP cross-check (2026-10-19)

## Why this experiment
The current worker_b checkpoint asks to extend the dependence-bounds oracle to four modes, but the repository history already contains that extension (commit `70366c2`) and an arbitrary-n exact forest fast path (commit `f979554`). Repeating the planned change would be duplicate work. This cycle pivoted to independently falsifying the newer forest formula.

## Method
For each n in {3,4,5,6}, generate 150 seeded random *feasible* joint distributions over all 2^n binary worlds using Dirichlet draws with varying concentration. Construct a random forest by attaching each vertex to an earlier vertex with probability 0.75. Derive the marginal and edge-joint probabilities from the generated distribution. Compare:
1. the forest formula in `tools/dependence_bounds.py` (reimplemented independently);
2. the minimum/maximum probability of all failures from a separate `scipy.optimize.linprog(method="highs")` atom-level LP.

Seed: 6419. Tolerance: 2e-7. SciPy is test-only; the production implementation remains dependency-free.

## Observed results
- **600 / 600** feasible forest cases matched the independent LP (150 per n).
- Largest absolute difference: **2.22e-16**.
- The experiment supports the forest fast path over this random sample, but is not a proof of the formula and does not exercise cyclic graphs or infeasible inputs.
- No evidence of a bug was found in this test; do not change production code on the strength of passing tests.

## Recovery and next step
Reproduce with the companion `tools/research/forest_lp_crosscheck.py` using Python, NumPy, and SciPy. To test production code directly rather than a reimplementation, add an import of `all_fail_bounds` from `tools/dependence_bounds.py` and compare all three values. Next priority: adversarial cyclic n=4 cases and boundary infeasibility, where the vertex-enumeration path has different numerical risks.

## Safety
No user data, credentials, unrelated repositories, or external actions involved. Only this sandbox branch is affected.
## Numerical boundary follow-up (separate adversarial probe)
A second local probe generated 3,000 Dirichlet distributions per n=2..6 with extreme concentration values {0.001, 0.01, 0.1, 1, 10} and checked all marginal/pairwise Frechet inequalities using ordinary double-precision sums. Among 105,000 pair checks, **1,853** numerically derived inputs appeared to violate a bound, by at most **3.33e-16**. Example: P(A)=0.0000033260366784082507, P(B)=1.0, P(A&B)=0.0000033260366784082507; floating-point P(A)+P(B)-1 evaluates to 0.000003326036678519273. The strict production validator would reject these rounded inputs although the original sampled joint distribution was feasible. This does **not** establish a mathematical error in the solver: the rounded constraints are formally inconsistent. It exposes an input-precision contract issue. Keep strict feasibility semantics; investigate explicit input precision/rounding policy rather than silently loosening the constraint tolerance.
