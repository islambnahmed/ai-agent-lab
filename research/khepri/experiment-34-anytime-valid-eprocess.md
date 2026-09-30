# Khepri Experiment 34 — Anytime-valid evidence under optional stopping

## Question
Experiment 33 showed that separate per-cycle alpha spending cannot keep a fixed lifetime false-positive budget and a constant positive per-cycle alpha forever. Can a simple sequential e-process accumulate evidence without assigning a fresh alpha to every cycle?

## Construction
For observations X_t that are independent N(mu, 1), test H0: mu <= 0 with the fixed betting factor

E_t = product_i exp(lambda X_i - lambda^2/2), lambda = 0.5.

Under the boundary null mu=0, E_t is a nonnegative martingale with E[E_t]=1. Ville's inequality therefore gives

P_0(sup_t E_t >= 1/alpha) <= alpha.

I used alpha=0.05, so the evidence threshold was 20. The stopping rule was deliberately optional: stop whenever the running e-value first crosses 20.

## Executed simulation
Local deterministic Monte Carlo, Python stdlib, seed 20260930 for the main comparison, 10,000 runs, horizon 500:

- null mu=0: crossing rate 0.0373
- alternative mu=0.25: crossing rate 0.7679; median crossing time among detections 56
- alternative mu=0.5: crossing rate 1.0000; median crossing time 21

A second null stress check (seed 123, 5,000 runs per horizon) gave crossing rates:
- horizon 50: 0.0350
- 100: 0.0356
- 500: 0.0370
- 2000: 0.0422

These Monte Carlo values are consistent with, but do not prove, the <=0.05 theoretical bound.

## What changed from Experiment 33
This architecture does not spend a new alpha_t each cycle. Evidence compounds in one process, and looking repeatedly / stopping when the threshold is crossed is part of the guarantee under the stated model.

So Experiment 33's impossibility result was about a particular architecture (infinitely many separate tests with summable alpha), not about indefinite monitoring itself.

## Counterexample / limitation
The guarantee is model-dependent. The factor exp(lambda X-lambda^2/2) relies on a sub-Gaussian/normal-style mgf bound and appropriate conditional behavior. Heavy tails, dependence, drift, data-dependent lambda chosen without a valid predictable construction, or reusing/adaptively selecting data can break calibration.

Also, fixed lambda=0.5 is tuned toward a particular effect scale. Small effects accumulate evidence slowly; a badly chosen lambda sacrifices power even though type-I control may remain valid under the model.

## Transfer lesson
The reusable capability is not "use this formula everywhere." It is: for long-lived monitoring, seek a nonnegative supermartingale/e-process whose validity survives optional stopping, then separately test its assumptions and power under the actual data-generating process.

## Next direction
Attack robustness rather than optimize the same Gaussian example: test what happens under heavy-tailed nulls and whether a bounded/robust e-process can preserve validity with weaker assumptions.
