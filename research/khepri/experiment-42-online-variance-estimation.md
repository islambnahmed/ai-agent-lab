# Experiment 42 — Online variance estimation stress test

Date: 2026-10-06

## Question
Can the variance-adaptive bounded-influence evidence process from the previous cycle remain empirically calibrated when conditional variance is not known and must be estimated online?

## Setup
- 12,000 Monte Carlo paths, horizon 300, alpha=0.05, eta=0.12.
- Evidence increment: psi(eta X_t) - 0.5 eta^2 vhat_t.
- psi(x)=sign(x) log(1+|x|+x^2/2).
- vhat_t is predictable: an EWMA of past squared observations only.
- Two null environments: alternating block heteroskedastic Gaussian variance; abrupt low-to-high variance jump.
- Oracle uses true conditional variance only as a reference.

## Results
Alternating blocks:
- oracle: 3.225% false crossing.
- EWMA lambda=.02, no inflation: 4.908%.
- EWMA lambda=.05, no inflation: 4.067%.
- EWMA lambda=.10, no inflation: 3.650%.
- EWMA lambda=.20, no inflation: 3.492%.
- lambda=.05 with 1.5x inflation: 1.150%.

Abrupt variance jump:
- oracle: 3.458%.
- EWMA lambda=.05, no inflation: 6.292% (fails 5% target).
- 1.5x inflation: 2.342%.
- 2x inflation: 0.900%.

## Interpretation
A plain predictable EWMA can look calibrated under recurring heteroskedasticity yet fail after an abrupt upward variance shift because it necessarily lags. This is a concrete counterexample to treating a point variance estimate as a safe compensation process.

Conservative inflation repaired this particular simulation, but a fixed multiplier is not a proof and can sacrifice power. The reusable lesson is stronger: anytime-valid evidence needs a predictable upper-confidence process for conditional variance (or a construction that avoids needing a point variance estimate), not merely an online variance forecast.

## Next high-value question
Construct/test an upper-confidence variance process with explicit coverage accounting, then evaluate false crossing and power under abrupt jumps, asymmetric heavy tails, and variance drift.