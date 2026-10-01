# Experiment 44 — finite-variance lower bound as a design benchmark

## Question
Once a numerical variance bound V is known, what *minimum* sample scale is unavoidable before a uniformly valid mean test can have useful power?

## Construction
Consider two distributions that produce the same all-ones prefix:
- P1: X=1 deterministically (mean 1).
- P0: X=1 with probability 1-p and X=-(1-p)/p with probability p (mean 0).

For P0, Var(X)=(1-p)/p. Setting p=1/(V+1) gives Var(X)=V exactly.

For N samples, event E = "all observations equal 1" has
P0(E)=(1-p)^N=(V/(V+1))^N,
while P1(E)=1.

Any test with type-I error <= alpha under every mean-zero distribution with variance <=V can reject on E with conditional probability at most alpha/P0(E). Therefore its power against P1 is at most alpha/P0(E) as long as E is the only observed path under P1.

To permit power >=1-beta, necessarily
(V/(V+1))^N <= alpha/(1-beta),
so
N >= log(alpha/(1-beta)) / log(V/(V+1)).

This is a lower bound on *any* method, not Chebyshev specifically.

## Numbers (alpha=.05, desired power=.8)
V=1: N>=4.00 -> 5 integer samples.
V=9: N>=26.31 -> 27.
V=99: N>=276.11 -> 277.
V=999: N>=2771.20 -> 2772.

Asymptotically N ≈ (V+1) log((1-beta)/alpha). For alpha=.05, power=.8, coefficient is log(16)=2.773.

## Counter-check / correction
Earlier Experiment 43 used the ambiguity threshold P0(E)<=alpha, corresponding roughly to allowing near-certain rejection on E. That is useful for identifiability intuition but is not a complete power benchmark. Adding a target beta makes the operational lower bound precise.

## Transfer
The same indistinguishability argument applies to sequential procedures stopped by time N: on E, their entire observed history is identical under P0 and P1. Optional stopping cannot beat this information lower bound.

## Durable lesson
Known variance restores finite-sample identifiability, but it also imposes an unavoidable O(V log(1/alpha)) sample scale in the worst case. Benchmark candidate robust sequential methods against this minimax scale rather than against Normal/t-distribution power alone.
