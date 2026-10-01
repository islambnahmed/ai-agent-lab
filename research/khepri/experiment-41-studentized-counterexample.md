# Experiment 41 — Studentized alpha-spending counterexample

## Candidate
At each time n, use the sample mean and sample standard error, with alpha_n = 0.05 * 6/(pi^2 n^2), and reject when the lower normal-approximation bound is above zero.

## Benign simulations
10,000 mean-zero paths, horizon 256, starting at n=10:
- Normal: naive repeated 1.96-SE crossing 0.207; alpha-spending 0.0064.
- scaled t(3): 0.1951; alpha-spending 0.0036.
- centered exponential: 0.101; alpha-spending 0.0006.

With mean shift +0.5, alpha-spending appeared powerful: Normal 0.9999 detection (median crossing 59), scaled t(3) 0.9953 (median 34), shifted exponential 1.0000 (median 72).

## Adversarial finite-variance benchmark
Let X=1 with probability 1-p and X=-(1-p)/p with probability p. This has mean exactly zero and finite variance. Before the rare compensating observation arrives, empirical variance can be zero while the sample mean is positive.

20,000 null paths, horizon 256:
- p=.01: crossing 0.9039
- p=.005: crossing 0.95145
- p=.002: crossing 0.9809

The intended lifetime false-positive target was 0.05.

## Falsified claim
Summable alpha spending plus sample-standard-error normal boundaries is not a distribution-free sequential finite-variance mean test. Alpha spending can compose valid per-look tests; it cannot repair a per-look approximation invalid under the stated distribution class.

## Reusable lesson
Future finite-variance sequential-mean candidates must be attacked with rare-compensating-outlier families, including the sign-reversed version. Symmetric t families alone gave false reassurance here.

## Direction
Retire naive Studentization. Only compare methods whose finite-sample assumptions explicitly cover the tested distribution class, and run this adversarial benchmark before power comparisons.
