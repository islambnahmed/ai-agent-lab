# Khepri Exp62 — Valid-factor reset after positivity audit

## Question
Can predictable online scale adaptation survive Exp61's positivity correction when the one-step factor is genuinely nonnegative on unbounded support?

## Construction A: Gaussian/sub-Gaussian e-factor
For a conditionally 1-sub-Gaussian null with mean <= 0, use

    E_t(lambda_t) = exp(lambda_t X_t - lambda_t^2/2), lambda_t >= 0.

If lambda_t is measurable from the past, conditional expectation is <= 1. The factor is strictly positive for every real X_t, so it avoids Exp61's quadratic-factor failure.

Adaptive learner tested:

    lambda_t = max(0, S_{t-1}/(t-1+c)), c=100.

Threshold: wealth >= 20 (alpha=.05). 5,000 Monte Carlo paths, horizon 10,000, Gaussian variance 1.

Results (detection probability, median hit time among hits):
- null mu=0: 0.0220 false-alarm rate, median 850.
- mu=.05: adaptive .9810 / 2703; oracle lambda=.05: .9872 / 1801.
- mu=.10: adaptive 1.000 / 703; oracle: 1.000 / 455.
- mu=.20: adaptive 1.000 / 223; oracle: 1.000 / 118.

A t^.75 regularizer (3*t^.75 in the denominator) did not dominate c=100: at mu=.05 it was .9798 / 3033 and at mu=.10 1.000 / 799.5. This is a counterexample to carrying Exp60's preferred schedule across factor families.

## Competing explanation / limitation
The exponential construction is not valid for arbitrary Student-t(3) observations under the same sub-Gaussian null assumption: the t3 mgf does not exist away from zero. Thus merely replacing the quadratic factor with an exponential factor fixes positivity but not heavy-tail robustness.

## Construction B: bounded-score robustification
To test transfer, transform Y_t=tanh(X_t), so Y_t is in [-1,1]. Under a symmetric zero-location null, E[Y_t]=0, and Hoeffding's lemma gives

    exp(lambda_t Y_t - lambda_t^2/2)

conditional expectation <=1 for predictable lambda_t. This is a different/null-class assumption, stated explicitly.

Using the same c=100 learner and 5,000 paths:
Gaussian:
- mu=.05: adaptive .7428 / 6033.5; fixed oracle-score lambda≈E[tanh(X)]=.03039: .8772 / 5363.5.
- mu=.10: adaptive 1.000 / 1820.5; oracle 1.000 / 1467.
- mu=.20: adaptive 1.000 / 507; oracle 1.000 / 367.

variance-normalized Student-t(3):
- mu=.05: adaptive .9708 / 5002; oracle-score lambda≈.03595: .9774 / 4207.
- mu=.10: adaptive 1.000 / 1291; oracle 1.000 / 1075.
- mu=.20: adaptive 1.000 / 382; oracle 1.000 / 275.

## Durable lesson
Exp61 does not kill predictable adaptation. It forces a separation between:
1. factor validity for the assumed null class,
2. online learning regret,
3. robustness/efficiency under alternative distributions.

A valid positive factor restored the predictable learner on Gaussian data. Heavy-tail transfer requires either an explicit bounded-score/null-symmetry construction or a different robust e-process; it cannot be inferred from Gaussian validity.

## Next discriminating experiment
Compare bounded-score choices (tanh clipping scale, hard clipping, Catoni-like scores) under a clearly specified heavy-tail null class, measuring both e-validity assumptions and efficiency. Do not optimize the regularizer again until the score/factor family is fixed.
