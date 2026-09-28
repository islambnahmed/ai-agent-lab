# Evidence Aggregation 17 — Exact Rational Boundary Oracle

## Question
Does the fixed `FEAS_TOL = 1e-12` introduced in experiment 16 actually separate floating-point roundoff from mathematically impossible probability constraints?

## Method
Built an independent exact oracle with Python `Fraction` arithmetic for n<=3. It enumerates the same probability worlds but solves candidate basic systems with exact Gaussian elimination, so feasibility decisions have no floating tolerance.

Two attacks were run:

1. **Feasible transfer set:** 1,000 random exact 3-mode distributions (denominator 1,000,000), deriving all marginals and all three pairwise joints. Float bounds were compared against exact rational bounds.
2. **Boundary adversary:** set P(A)=P(B)=0.1 and P(A&B)=0.1+delta for tiny positive deltas.

## Evidence
- Random feasible transfer set: **0 mismatches / 1,000** at a 1e-10 bound-comparison threshold.
- Exact oracle rejects every positive delta because P(A&B) cannot exceed min(P(A),P(B)).
- Current float implementation accepted delta=1e-13 and delta=5e-13 as feasible. Example: with delta=1e-13 it returned all-fail bounds (0.1000000000001, 0.1000000000001).
- It rejected larger tested deltas such as 1.1e-12.

Therefore experiment 16 fixed the original 1e-9 reproducer but did **not** remove the semantic gap; a fixed 1e-12 tolerance still intentionally blurs contradictions smaller than roughly that scale.

## Competing explanation tested
Removing tolerance entirely from the Frechet precheck risks rejecting mathematically valid decimal boundary inputs because binary floats can round the computed lower bound upward. Exhaustive hundredth-grid testing found 2,024 such lower-bound comparisons where direct zero-tolerance comparison would reject a valid exact-decimal boundary (for example 0.02 + 0.99 - 1).

## Better candidate
Use a tolerance tied to floating-point representation error for the cheap Frechet precheck rather than a fixed 1e-12. A prototype tolerance of:

`8 * max(ulp(p_i), ulp(p_j), ulp(q), ulp(lower), ulp(upper), ulp(1.0))`

produced **0 false rejects** over all hundredth-grid Frechet boundaries tested, while rejecting the 1e-13 contradiction that the current fixed tolerance accepts. At scale <=1 this tolerance is about 1.78e-15.

This is not yet a proof that 8 ulps is universally sufficient. The LP residual/non-negativity tolerances are a separate numerical question.

## Reusable lesson
Numerical validation should distinguish **representation error** from **model slack**. A fixed absolute epsilon silently changes the mathematical feasible set; an ulp-aware boundary check can preserve ordinary float roundoff without accepting much larger semantic contradictions.

## Next falsification target
Search adversarial decimal/rational inputs across magnitudes and near both Frechet boundaries to determine whether an ulp budget can be justified, then separately attack the Gaussian vertex solver's residual policy.
