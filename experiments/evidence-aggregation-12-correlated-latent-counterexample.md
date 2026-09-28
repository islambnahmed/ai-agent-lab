# Evidence Aggregation 12 — correlated latent-mode counterexample

## Question
How badly can the independent latent-failure oracle misstate evidence survival when latent failure modes are themselves dependent?

## Construction
Take two evidence paths:
- E1 fails iff latent mode A fails.
- E2 fails iff latent mode B fails.
- P(A fails)=P(B fails)=0.20.

The independent-mode oracle assumes P(A and B fail)=0.04, so it predicts:
- P(any evidence survives)=0.96
- P(all evidence survives)=0.64

Now hold both marginal failure rates fixed at 0.20 but change only their dependence.

### Perfect positive dependence
A and B always fail together:
- P(A and B fail)=0.20
- P(any survives)=0.80
- P(all survives)=0.80

Independent-oracle errors:
- any-survives: +0.16 (overconfident)
- all-survive: -0.16 (underconfident)

### Maximally negative dependence
A and B never fail together (possible because 0.20+0.20 <= 1):
- P(A and B fail)=0
- P(any survives)=1.00
- P(all survives)=0.60

Independent-oracle errors:
- any-survives: -0.04
- all-survive: +0.04

## General bound
For two failure modes with marginals pA and pB, the joint failure probability q is only constrained by the Frechet bounds:
max(0, pA+pB-1) <= q <= min(pA,pB).

Therefore:
- P(any evidence survives)=1-q
- P(all evidence survives)=1-pA-pB+q

With pA=pB=0.20, the honest interval without a dependence assumption is:
- P(any survives) in [0.80, 1.00]
- P(all survives) in [0.60, 0.80]

The independence point (0.96, 0.64) is merely one point inside those intervals, not a privileged truth.

## Falsification result
The independence assumption can produce materially wrong confidence even when every marginal failure probability is exactly correct. More evidence-path detail does not fix this if dependence among latent modes is unknown.

## Design consequence
For small graphs, the next oracle should accept either:
1. an explicit joint/factor model for dependent latent modes, or
2. uncertainty sets/bounds over dependence and return probability intervals.

When dependence is unknown, report bounds rather than a falsely precise scalar probability. A useful next experiment is to implement exact interval propagation for small binary latent graphs and compare it against the independent oracle on adversarial fixtures.
