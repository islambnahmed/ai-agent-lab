# Khepri Experiment 39 — Heavy-tail sequential evidence without hard clipping

## Question
Experiment 38 showed that clipping can restore bounded-input validity while silently changing the estimand. Can a bounded-influence transform retain useful sequential detection under an unbounded, finite-variance distribution without literal clipping?

## Reversible simulation
12,000 Monte Carlo paths, 300 observations/path, nominal alpha=0.05. Data were Student-t with 3 degrees of freedom scaled to variance 1 (unbounded, mean 0, finite variance).

I tested the influence transform
`psi(x)=sign(x) log(1+|x|+x^2/2)`
inside the candidate log process
`sum_t [psi(eta X_t) - eta^2/2]`.

This cycle is an empirical stress test, not a proof that the candidate is an e-process under only a variance assumption.

### Null crossing rates
- eta=0.08: 0.44%
- eta=0.12: 1.43%
- eta=0.18: 2.41%

All were below the nominal 5% threshold in this Student-t(3) stress case.

### Heavy-tail detection power (eta=0.12)
- mean shift 0.15: 64.78%
- mean shift 0.25: 98.33%
- mean shift 0.40: 100%

## Why this advances Experiment 38
Unlike hard clipping, the transform is not flat beyond a threshold; extreme observations retain graded influence. The experiment therefore supplies a concrete candidate direction for robust sequential evidence that does not simply replace X by a clipped estimand.

## Critical limitation / counterexample still required
Empirical calibration on Student-t(3) does not establish anytime validity. The compensation term eta^2/2 was borrowed as a candidate and needs a theorem under an explicit conditional moment class. Asymmetric heavy tails, conditional heteroskedasticity, and serial dependence can still break it.

## Durable lesson
The next useful move is no longer “clip harder.” Bounded-influence transforms can preserve substantial heavy-tail power while avoiding literal hard clipping, but the scientific claim must remain provisional until the transformed exponential factor is proved to have conditional expectation <=1 under a stated null class.

## Next experiment
Derive or import a valid Catoni-style exponential inequality under a conditional finite-variance assumption, then adversarially test asymmetric two-point/mixture distributions that saturate that assumption.
