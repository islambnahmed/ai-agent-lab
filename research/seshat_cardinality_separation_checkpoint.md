# Seshat checkpoint: cardinality-cut separation complexity

## Result

For a fully observed subset S of binary variables, define

- p_i = P(X_i=1)
- q_ij = P(X_i=1,X_j=1)
- mu(S) = sum_{i in S} p_i
- k = floor(mu(S))

Since K=sum_{i in S} X_i is integer-valued, its second moment obeys the lower convex envelope of z^2 on integers:

E[K^2] >= k^2 + (mu-k)(2k+1).

Using E[K^2]=sum p_i + 2 sum q_ij gives the violation score

V(S)=2k sum_{i in S} p_i - 2 sum_{i<j in S} q_ij - k(k+1).

V(S)>0 is therefore a sound infeasibility certificate.

## New separation observation

For fixed k, maximizing V(S) is a quadratic 0/1 subset-selection problem:

maximize 2k sum_i p_i x_i - 2 sum_{i<j} q_ij x_i x_j - k(k+1)

subject to
k <= sum_i p_i x_i < k+1,
and x_i x_j may be 1 only when pair (i,j) is observed if certificates are restricted to fully observed subsets.

Thus the hard part is not evaluating a certificate but separating over subsets. Treating global exact separation as automatically polynomial would be unjustified.

## Safe implementation strategy

Use bounded separation before the exact joint solver:

1. Test the full observed clique/component when applicable.
2. Enumerate fully observed subsets only up to a configurable small size r.
3. Evaluate V(S) in O(|S|^2), retaining the strongest witness.
4. If none violates, report only "no bounded cardinality violation found"; never infer feasibility.
5. Fall through to the exact solver.

For fixed r this costs O(n^r r^2) in the worst case and is complete for cardinality witnesses of size <= r.

## Witness payload

A reusable certificate should record:
- subset S
- mu
- k=floor(mu)
- observed E[K^2]
- integer lower bound on E[K^2]
- violation margin
- contributing p_i and q_ij

This makes rejection independently auditable.

## Research status

The inequality is proven from integrality of K. The bounded separator is sound by construction. No claim is made here that unrestricted strongest-cardinality-cut separation is polynomial or NP-hard; that complexity question remains open pending a formal reduction or literature match.
