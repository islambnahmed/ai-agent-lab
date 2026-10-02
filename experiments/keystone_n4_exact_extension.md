# Keystone experiment: exact n=4 feasibility envelope

Date: 2026-10-02

## Question

Is the existing vertex-enumeration solver in `tools/dependence_bounds.py` computationally reasonable for pairwise-constrained systems with four binary failure modes?

## Result

Yes. For n=4 there are 16 binary worlds. The equality system contains normalization, four marginal constraints, and up to six pairwise constraints.

The solver enumerates bases of size m from 16 worlds. Across possible pairwise-constraint counts, m ranges from 5 through 11. The worst combinatorial basis count is therefore

`max_m C(16,m) = C(16,8) = 12,870`.

With all six pairwise constraints, m=11 and only

`C(16,11) = 4,368`

bases are considered.

This is small enough to justify an exact n=4 extension without adding a third-party LP dependency.

## Regression target

For four events with

- P(A_i)=1/2 for every i
- P(A_i and A_j)=1/4 for every pair i<j

pairwise independence does not imply mutual independence. The tight all-fail interval is

`0 <= P(A1 A2 A3 A4) <= 1/6`.

Full independence would select 1/16, which is merely one feasible point inside the interval.

## Boundary

Do not generalize the same brute-force strategy to n=5. With 32 worlds and all marginals + pairwise constraints, m=16 and basis enumeration becomes

`C(32,16) = 601,080,390`.

For n>=5, use a real LP solver or a specialized formulation.

## Implementation recommendation

Raise the pairwise-constrained cap from n<=3 to n<=4 and add the four-event regression above. Keep n>=5 rejected until the solver architecture changes.
