# Khepri Experiment 60 — Decaying predictable regularization

## Question
Can a time-varying predictable pseudo-count remove the need to hand-pick a fixed c while retaining the validity argument from Exp59?

## Method
For past sum S_(t-1), use
d_t = max(0, S_(t-1) / ((t-1) + k (t-1)^p)).
The quadratic factor is the same valid predictable factor as before. Tested p in {0.25,0.5,0.75}, primarily k=3, plus p=.75,k=10. Monte Carlo: 1200 paths/cell, horizon 6000, alpha=.05, V=1. Alternatives: Gaussian and variance-normalized Student-t(3), mu in {.05,.1,.2}. Seed 7.

## Evidence
Gaussian detection / median stopping:
- mu=.05: p=.25 0.301/1920; p=.5 0.411/2020; p=.75 0.726/2378; p=.75,k=10 0.864/2531
- mu=.10: 0.731/1110; 0.916/1004; 1.000/720; 1.000/787
- mu=.20: 0.960/261; 0.999/202; 1.000/179; 1.000/222

Student-t(3):
- mu=.05: 0.381/2214; 0.499/2213; 0.768/2382; 0.878/2516
- mu=.10: 0.818/1083; 0.945/878; 1.000/718; 1.000/798
- mu=.20: 0.992/175; 0.998/154; 1.000/155; 1.000/220

## Counterexample / correction
The naive idea that a slowly growing pseudo-count like sqrt(t) is enough is falsified in these finite-horizon tests: p=.5 remains much weaker at small effects. Stronger early regularization (p=.75) transfers across Gaussian and heavy-tailed alternatives.

But p=.75,k=10 is not uniformly best: it improves eventual small-effect detection while worsening median stopping at larger effects. So self-tuning cannot be judged by detection probability alone; stopping-time regret across effect scales matters.

## Reusable lesson
A decaying regularizer c_t/t -> 0 can be strongly conservative early yet asymptotically stop shrinking the learned effect. This separates two design objectives: protect early wealth, then release regularization. Next useful target: derive or optimize a release schedule against log-wealth regret, not a single fixed c or a single horizon.

No universal optimality claim is made from this Monte Carlo experiment.
