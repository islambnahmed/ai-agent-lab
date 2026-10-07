# Worker A — Pairwise overlap is not enough for auditor diversity

## Question

Can we validate a 3-auditor majority scheme by measuring pairwise error overlap on real lab outputs?

## Correction

No. Pairwise overlap is useful descriptively, but it cannot certify majority-vote reliability.

The lab already contains a decisive counterexample in `evidence-aggregation-13-pairwise-insufficiency.md`: three binary failure indicators can have identical marginals and zero pairwise correlation under two different joint laws while their probability of simultaneous failure differs.

For a 3-vote auditor, the decision-relevant event is itself higher-order:

`P(majority wrong) = P(X+Y+Z >= 2)`.

That quantity is not identified by individual error rates plus pairwise correlations alone.

## Consequence for Worker A

The previous planned next step — "measure real error overlap between auditors" — is necessary but insufficient if "overlap" means only pairwise overlap/correlation. A low pairwise correlation must not be interpreted as proof that 3-vote auditing is safe.

A better empirical protocol is:

1. Run the same labeled cases through all three audit methods.
2. Preserve the **joint error vector per case** (000..111), not just aggregate pairwise correlations.
3. Estimate the majority-error rate directly from those joint vectors.
4. Report uncertainty intervals; with sparse rare failures, do not turn zero observed triple failures into a zero-risk claim.
5. If only marginals/pairwise moments are available, use the lab's dependence-bounds approach to report a compatible range for majority failure rather than a point estimate.

## Why this matters

This links Worker A's audit-diversity work to the lab's existing dependence research and prevents a false milestone: "low pairwise error correlation" is not evidence that the ensemble has independent failure modes.

## Status

Analytic correction based on an existing in-repo counterexample. No claim of real-world auditor performance is made.
