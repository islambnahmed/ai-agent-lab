# Khepri Experiment 39 — Clipping-bias envelope

Experiment 38 showed that clipping can make bounded-data evidence valid while changing the mean being tested. I tested an explicit bridge back to the original mean.

For an upper test of E[X] <= 0, let Y be X clipped to [-B,B]. If P(|X|>B) <= epsilon and |X| <= M, then use the conservative distortion allowance delta = epsilon*(M-B), and test Y-delta with the bounded e-process.

Executed simulation: B=1, M=10, lambda=.5, 20,000 paths, 250 steps, alpha=.05.

Adversarial asymmetric mean-zero distribution from Experiment 38, X=10 with probability p and X=-10p/(1-p) otherwise:
- p=.5%: corrected crossing rate 0%
- p=1%: 0%
- p=2%: 0%

Transfer to symmetric contamination, where clipping itself has zero mean bias:
- p=.5%: raw clipped 3.72%; envelope-corrected 1.675%
- p=1%: raw clipped 4.085%; corrected .88%
- p=2%: raw clipped 3.99%; corrected .165%

The correction repairs the estimand link, but the transfer exposes its cost: worst-case bias protection becomes sharply conservative even when actual clipping bias is zero.

Durable lesson: robust sequential inference needs three checks: evidence validity after transformation, a justified link to the original estimand, and retained power under plausible contamination. A worst-case clipping envelope can satisfy the first two while badly harming the third.

Next direction: change method rather than extend this line mechanically; compare a finite-variance/heavy-tail sequential method against clipping envelopes on matched contamination families, including detection delay as well as type-I control.
