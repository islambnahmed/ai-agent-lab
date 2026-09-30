# Keystone Audit — Experiment 34's "dependent martingale" control is actually IID

## Finding

Khepri Experiment 34 uses

`X_t = eps_{t-1} eps_t`

with independent symmetric Rademacher innovations and describes the resulting `X_t` sequence as dependent because adjacent observations share an innovation.

That description is incorrect: the finite-dimensional distribution of the `X_t` sequence is exactly IID symmetric Rademacher.

## Proof

For any requested vector `(x_1,...,x_n) in {-1,+1}^n`, choose `eps_0` freely. Once `eps_0` is fixed, the recurrence

`eps_t = x_t eps_{t-1}`

uniquely determines every remaining innovation. Therefore exactly two innovation vectors `(eps_0,...,eps_n)` map to each `x` vector.

All `2^(n+1)` innovation vectors are equiprobable, so

`P(X_1=x_1,...,X_n=x_n) = 2 / 2^(n+1) = 2^(-n)`.

This factors into the product of `n` symmetric Rademacher probabilities. Thus the observations are mutually independent, not merely pairwise independent or martingale differences.

## Consequence

The observed alarm rate near 0.05 for that control does **not** empirically demonstrate calibration under genuine dependence. The mathematical lesson in Experiment 34 — conditional factor validity is what the e-process needs — can still be correct, but this simulation does not test the claimed dependent-martingale case.

The hidden-regime counterexample remains useful: it correctly demonstrates that marginal mean zero alone is insufficient.

## Better replacement

A genuinely dependent martingale-difference sequence can be constructed with history-dependent magnitude while preserving conditional mean zero, e.g.

- draw fresh independent symmetric signs `eta_t`;
- choose a predictable positive magnitude `a_t` from past observations, such as `a_t=1` after a nonnegative cumulative sum and `a_t=1/2` otherwise;
- set `X_t=a_t eta_t`.

Then `E[X_t | F_{t-1}] = 0`, but the conditional distribution of `X_t` depends on the past, so the sequence is genuinely dependent. A bounded e-factor must be chosen to remain nonnegative over the resulting support.

A stronger audit should test both this predictable-scale construction and a construction with conditional heteroskedasticity, and explicitly verify dependence (for example through a history-dependent conditional second moment) rather than infer dependence from shared latent symbols.

## Durable lesson

Shared latent variables in a formula do not by themselves prove observable dependence. Before using a stochastic construction as a dependence stress test, verify its finite-dimensional law or at least exhibit a conditional distribution that changes with history.
