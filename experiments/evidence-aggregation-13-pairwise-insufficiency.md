# Evidence Aggregation 13 — Pairwise Independence Is Not Enough

## Question
If every latent failure has a known marginal probability and every pair has zero correlation, is system reliability determined?

## Construction
Let X,Y,Z be binary failure indicators.

**Distribution A (fully independent fair bits):** all 8 states have probability 1/8.

**Distribution B (even-parity law):** states 000, 011, 101, 110 each have probability 1/4; all other states have probability 0.

For both distributions:
- P(X=1)=P(Y=1)=P(Z=1)=1/2.
- For every pair, P(X=1,Y=1)=1/4, so covariance and correlation are 0.
- Therefore every pair is independent.

But higher-order outcomes differ:
- P(no failures = 000): A = 1/8; B = 1/4.
- P(all three fail = 111): A = 1/8; B = 0.
- P(at least one failure): A = 7/8; B = 3/4.

## Result
Marginals plus all pairwise correlations do not identify joint reliability. Pairwise independence does not imply mutual independence.

## Design consequence
A single confidence estimate is unjustified when higher-order dependence is unknown. The next useful tool is a **bounds oracle**: optimize the target event probability over all joint distributions compatible with known constraints (normalization, marginals, and optional pairwise moments). For small binary systems this is a linear program over 2^n state probabilities.

This changes the project direction from inventing increasingly elaborate confidence heuristics to reporting decision-relevant uncertainty intervals and testing how quickly additional structural assumptions tighten them.
