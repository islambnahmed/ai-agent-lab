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

Then `E[X_t | F_{t-1}] = A_{t-1} E[eps_t]=0`, while the conditional distribution of `X_t` changes with the past, giving genuine dependence.

For the bounded betting factor `1 + lambda X_t`, with `lambda <= 1`, each factor stays nonnegative and has conditional expectation 1. The product is therefore a nonnegative martingale, so Ville's inequality supplies the same anytime type-I guarantee.

## Empirical check and diagnostic correction

A follow-up simulation used 20,000 independent runs of length 500, `lambda=0.25`, and alarm threshold 20. The observed anytime alarm rate was **0.0443**, consistent with the 0.05 Ville bound.

The first version of this audit suggested `corr(|X_{t-1}|, |X_t|)` as a dependence diagnostic. That suggestion was wrong for this construction: `|X_t| = A_{t-1}` depends on `eps_{t-1}`, while `|X_{t-1}|` depends on an earlier sign, so their adjacent absolute-value correlation is zero in the idealized process.

A diagnostic aligned with the construction is `corr(X_{t-1}, |X_t|)`. A separate one-million-step simulation gave approximately **0.8574**, exposing the strong dependence that raw `corr(X_{t-1},X_t)` and adjacent absolute-value correlation can miss. Analytically, with magnitudes 1 and 0.25 this correlation is nonzero because the sign of `X_{t-1}` reveals `eps_{t-1}`, which determines the next magnitude.

## Recommended correction

Re-run Experiment 34 with this or another demonstrably dependent martingale-difference sequence. Pair the alarm rate with a dependence diagnostic chosen from the process construction rather than a generic autocorrelation. Keep the hidden-regime case as the negative control.

This audit corrects both the original positive-control label and its own first diagnostic recommendation; it does not invalidate the experiment's central conditional-validity lesson.
