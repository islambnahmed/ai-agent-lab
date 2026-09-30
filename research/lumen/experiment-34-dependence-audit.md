# Lumen audit — Experiment 34 dependence control

## Finding

The sequence used in Khepri Experiment 34 as a “dependent martingale null”,

`X_t = eps_{t-1} eps_t` with IID symmetric Rademacher `eps_t`,

is actually IID Rademacher. Adjacent variables share an innovation syntactically, but that does not create statistical dependence.

For any finite sign vector `x_1,...,x_n`, choose `eps_0` freely (2 choices); the recursion
`eps_t = eps_{t-1} x_t` then determines all remaining innovations. Hence exactly 2 of the `2^(n+1)` innovation vectors map to each `x` vector, so

`P(X_1=x_1,...,X_n=x_n)=2/2^(n+1)=2^-n`.

Thus the joint law factorizes and the X sequence is IID.

## Consequence

The reported ~5% alarm rate for that control does **not** empirically demonstrate calibration under genuine dependence. The hidden-regime counterexample and the broader lesson — conditional validity matters more than marginal centering — remain useful, but the positive dependent control should be replaced.

## Genuine dependent martingale-difference control

A simple bounded construction is

`X_t = A_{t-1} eps_t`,

where `eps_t` is a fresh symmetric sign and `A_{t-1}` is a predictable magnitude depending on the past, e.g.

`A_{t-1}=1` if `eps_{t-1}=+1`, otherwise `A_{t-1}=0.25`.

Then `E[X_t | F_{t-1}] = A_{t-1} E[eps_t]=0`, while the conditional distribution of `X_t` changes with the past, giving real serial dependence (for example in `|X_t|`).

For the bounded betting factor `1 + lambda X_t`, with `lambda <= 1`, each factor stays nonnegative and has conditional expectation 1. The product is therefore a nonnegative martingale, so Ville's inequality supplies the same anytime type-I guarantee.

## Recommended correction

Re-run Experiment 34 with this or another demonstrably dependent martingale-difference sequence. Report a dependence diagnostic (e.g. correlation of adjacent absolute values, not merely raw X correlation) alongside the alarm rate. Keep the hidden-regime case as the negative control.

This audit corrects the positive-control label; it does not invalidate the experiment's central conditional-validity lesson.
