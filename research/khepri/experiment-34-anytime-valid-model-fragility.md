# Khepri — Anytime-valid does not mean model-robust

## Correction
The sequential e-process direction after Experiment 33 solves repeated peeking only under its supermartingale/model assumptions. It must not be described as generally robust to arbitrary heavy tails, serial dependence, or drift.

## Executed counterexample evidence
A reversible local simulation (4,000 paths per case, 300 observations/path, nominal alpha=0.05, Gaussian likelihood-ratio mixture) produced approximate false-alarm rates:
- iid N(0,1): 2.5%
- iid distribution with 1% symmetric ±20 shocks: 35.5%
- Gaussian AR(1), rho=0.5: 25.6%
- Gaussian AR(1), rho=0.8: 51.1%
Under the intended iid Gaussian model with mean improvement 0.25, detection was about 96.1%.

These numbers are empirical diagnostics, not universal constants.

## Why it fails
The Gaussian e-value factor exp(lambda X - lambda^2/2) has conditional expectation <=1 under the intended conditional Gaussian/sub-Gaussian null. Heavy shocks violate the moment-generating-function bound. Positive serial dependence violates the conditional-null structure even when the unconditional mean remains zero. Ville's inequality cannot rescue an object that is no longer a valid nonnegative supermartingale.

## Reusable design rule
Any long-lived evolution audit must state the *conditional* assumptions that make its e-process valid. "Anytime-valid" describes optional-stopping validity conditional on those assumptions; it is not a synonym for distribution-free or dependence-robust.

## Next direction
Do not patch the Gaussian process with arbitrary clipping and call it robust. A defensible replacement needs an explicit weaker assumption class (for example bounded observations with a conditional-mean null, or another justified predictable bound), then a fresh adversarial test against that exact class. Dependence/drift require their own null formulation rather than cosmetic robustification.
