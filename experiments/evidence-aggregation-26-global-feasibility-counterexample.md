# Experiment 26 — Pairwise-valid constraints can be globally impossible

## Question
Are marginal + pairwise Frechet checks sufficient to establish that a three-mode dependence specification is globally feasible?

## Counterexample
Let P(A)=P(B)=P(C)=0.1 and:
- P(A∩B)=0
- P(A∩C)=0.1
- P(B∩C)=0.1

Every pair individually satisfies its Frechet interval [0, 0.1].

But P(A∩C)=P(A)=0.1 forces A⊆C almost surely, and P(B∩C)=P(B)=0.1 forces B⊆C almost surely. The zero A∩B intersection is locally possible, yet the exact three-way interval exposes the contradiction:

For t=P(A∩B∩C),
lower = max(0, qAB+qAC-pA, qAB+qBC-pB, qAC+qBC-pC) = 0.1.
upper = min(qAB, qAC, qBC, 1-pA-pB-pC+qAB+qAC+qBC) = 0.

Thus t must simultaneously satisfy t≥0.1 and t≤0: impossible.

## Verification
An independent exact-rational implementation of the closed-form three-event interval was checked on 10,000 randomly generated valid joint distributions. In every case the realized triple intersection lay inside the derived interval.

## Reusable lesson
Pairwise consistency is necessary but not sufficient for global consistency. For n=3 with all three pairwise intersections specified, a cheap exact precheck is available: compute the triple-intersection lower/upper interval and reject when lower>upper. This should precede floating-point vertex enumeration, both to catch structural contradictions exactly and to separate semantic infeasibility from numerical tolerance.

## Next engineering step
Add a three-event global-feasibility precheck to tools/dependence_bounds.py, then regression-test this counterexample plus valid boundary cases before considering general n>3 feasibility machinery.
