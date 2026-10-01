# Four-way failure risk under pairwise independence

Keystone experiment: extend the dependence-bounds question to four fair binary failure modes without changing production code.

## Setup

Let X1,...,X4 be binary failure indicators with

- P(Xi=1)=1/2 for every i;
- P(Xi=Xj=1)=1/4 for every pair i<j.

Thus every pair is independent. No mutual-independence assumption is made.

I enumerated all 16 binary worlds and solved the exact finite LP over their probability masses, with normalization, four marginal constraints, and six pairwise-joint constraints.

## Exact result

The feasible range for the four-way joint failure probability is

    0 <= P(X1=X2=X3=X4=1) <= 1/6.

Therefore the probability that at least one path survives is exactly bounded by

    5/6 <= P(any survives) <= 1.

Full mutual independence would instead give all-fail probability 1/16 and survival probability 15/16. That point is feasible, but pairwise independence alone permits all-fail risk 8/3 times larger:

    (1/6)/(1/16) = 8/3.

## Why this matters

The existing n=3 regression already shows that pairwise independence does not imply mutual independence. The n=4 experiment shows the practical gap can widen materially: multiplying marginal probabilities can understate simultaneous-failure risk even when every pair passes an exact independence constraint.

The current vertex-enumeration implementation is structurally generic but intentionally rejects pairwise-constrained n>3. This experiment is evidence that n=4 support would be useful, but it does not justify blindly lifting the cap: naive basis enumeration can grow combinatorially. A bounded n=4 implementation should therefore be benchmarked for runtime before changing the public contract.

## Reproduction recipe

Enumerate worlds in {0,1}^4. Use one probability variable per world. Constrain all variables nonnegative and impose:

1. sum of world probabilities = 1;
2. each marginal sum = 1/2;
3. each of the six pairwise intersection sums = 1/4.

Minimize and maximize the mass on world (1,1,1,1). Exact vertex enumeration returns 0 and 1/6.

## Next falsification target

Search unequal marginals and sparse pairwise constraints for cases where the independence plug-in falls outside a narrow-looking but valid LP interval, and measure how quickly naive vertex enumeration degrades as constraints approach full pairwise coverage.
