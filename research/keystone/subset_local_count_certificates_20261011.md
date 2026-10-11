# Keystone: subset-local count-polynomial certificates (2026-10-11)

## Goal and distinction
We know only individual binary failure rates p_i and pairwise joint rates q_ij. Previous work gave (a) a second-order Bonferroni bound for arbitrary subsets and (b) a count-polynomial bound using the *full* set of events after averaging moments. This experiment combines the two: optimize a count-polynomial certificate on **every subset**, retaining heterogeneous information rather than averaging all systems together.

## Certified inequality
For any subset S of size k>=2, K_S = sum_{i in S} 1{E_i}, and integer r in {0,...,k-2}, the integer-valued polynomial (K_S-r)(K_S-r-1) is nonnegative for every K_S=0,...,k, and is (k-r)(k-r-1) when K_S=k. Thus

P(all n events) <= P(K_S=k)
 <= [2 sum_{i<j in S} q_ij - 2r sum_{i in S} p_i + r(r+1)] / [(k-r)(k-r-1)].

For singleton S, use p_i. Minimize over S,r using exact rational arithmetic. This does not require independence or exchangeability. It is a certified *upper bound*, not generally the sharp maximum compatible with all pairwise moments.

## Reproducible strict improvement
Take five failure events with a feasible joint law defined by **seven equiprobable 5-bit masks** (bit i indicates failure of event i):
16, 7, 9, 19, 4, 29, 11.

This implies p=(5,3,3,3,3)/7, and pair intersections q_01=3/7, q_02=2/7, q_03=3/7, q_04=2/7; every pair among indices 1,2,3,4 has q=1/7.

* Previous minimum across second-order subset Bonferroni certificates: 1/7.
* Previous full-set count-polynomial upper bound: 1/7.
* New subset-local count-polynomial upper bound: **1/21**, using S={1,2,3,4}, r=1.

This is a 3x tighter certified upper bound from identical moment data. The full-atom SciPy LP maximum for this particular moment table is **zero**: the new bound is still not globally sharp. In a separate four-event pairwise-independent example p_i=1/2, q_ij=1/4, the new bound 1/6 is sharp (LP confirms), improving Bonferroni's 1/4.

## Verification (local, not CI)
Five unittest methods passed, including 175 deterministic random feasible laws (35 each for n=2..6) checked against independent SciPy HiGHS full-atom LP maxima, plus exact certificate verification and invalid-input tests. Every certified bound was >= the LP maximum (1e-8 numerical tolerance) and <= the previous subset Bonferroni bound. A local n=12 pairwise-independent example took ~0.10s; this is a single-machine preliminary measurement, not a performance guarantee.

## Implementation and limitations
Algorithm: DP over bitmask subsets caches mu(S)=sum p_i and tau(S)=sum q_ij; evaluate k-1 polynomials per subset, O(n*2^n) exact rational operations and O(2^n) memory. Guard n<=18. Inputs reject floats for exact certification. Pairwise Frechet checks are **not** sufficient to establish global moment feasibility; use full-atom LP for small n when feasibility and tightness matter. This is a mathematical risk envelope, not a measured failure probability of real lab agents.

## Recovery
Code and tests were executed locally on 2026-10-11; keep the accompanying Python implementation and unittest file with this note when possible. This report is evidence of a local experiment, not a claim of deployment or CI integration.
