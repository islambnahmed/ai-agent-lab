# Experiment 03 — Membership-query lower bound

## Question
Can a better compositional representation by itself remove the exponential worst case observed when actively learning Boolean conjunctions?

## Setup
Hypotheses are conjunctions over d Boolean variables. Each variable is positive, negative, or absent, so there are 3^d hypotheses. The learner may issue ordinary membership queries: choose a complete Boolean input x and observe only the target label f(x).

Previous exhaustive greedy-query measurements were:
- d=3: 27 hypotheses, mean 5.07 queries, worst 7
- d=4: 81 hypotheses, mean 7.57, worst 15
- d=5: 243 hypotheses, mean 11.28, worst 31
- d=6: 729 hypotheses, mean 17.12, worst 63

## Structural diagnosis
The worst case is not merely a bad representation.

The class contains 2^d fully specified conjunctions, one for every Boolean vector a. Such a hypothesis is true on exactly one input: x=a.

Consider a target chosen from those singleton hypotheses. A negative membership answer at x eliminates only the singleton target x. Until a positive answer is observed, all other unqueried singleton targets remain consistent. Therefore an adversary can answer negative to the first 2^d-1 distinct queries, forcing any deterministic exact learner to use 2^d-1 queries in the worst case (and the final remaining singleton is then identified).

This exactly matches the measured 7, 15, 31, 63 pattern.

## Consequence
The proposed next move, "use compositional representation to turn the same membership-query problem polynomial," is falsified. Factorized storage may reduce memory or computation, but cannot remove this information bottleneck while the observation interface remains one complete input -> one binary label and the target class still includes singleton conjunctions.

## What must change
To obtain polynomial identification, at least one assumption/interface must change. Candidate experiments:
1. richer queries (e.g. equivalence/counterexample or partial-assignment queries);
2. a restricted target class that excludes near-singletons / bounds conjunction width;
3. a distributional objective (high predictive accuracy rather than exact identification);
4. structural priors that assign negligible mass to pathological singleton targets.

## Decision
Do not spend more cycles optimizing greedy membership-query selection for this class. Next experiment should compare one changed interface against the same lower-bound family and preregister the resource/accuracy target before implementation.
