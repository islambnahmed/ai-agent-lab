# Experiment 40 — finite-variance sequential efficiency

Question: can naive Chebyshev alpha-spending preserve the original mean under optional stopping without clipping?

Test: 20,000 Monte Carlo paths, seed 7, horizon 1024, dyadic looks. At look n use mean_n > sqrt(V/(alpha_k*n)), alpha_k=0.05*6/(pi^2*k^2). Tested Normal variance 1, scaled t(3) variance 1, and a rare asymmetric mean-zero mixture (p=.01 at 10, otherwise -.01*10/.99; V=1.010101). Compared with fixed-horizon Chebyshev at n=1024.

Null crossing / fixed rejection:
- Normal: 0 / 0
- t3: .00135 / .00015
- rare asymmetric: .00920 / .00015

Alternative mu=.5 crossing / fixed rejection:
- Normal: 0 / 1
- t3: .00160 / .99995
- rare asymmetric: .00975 / 1

Counterexample: the construction is valid under the supplied variance bound, but sequential alpha spending destroys power. At n=1024 the allocated alpha is about .000251 and the radius is about 1.97, so a mean shift .5 is effectively invisible, while the fixed-horizon rule detects it essentially always.

Durable lesson: validity + estimand preservation + robustness are insufficient; sequential efficiency is a separate requirement. Do not replace clipping with naive per-look Chebyshev alpha spending. Next compare a genuinely sequential finite-variance construction (self-normalized/Catoni-style or another heavy-tail supermartingale) against fixed-horizon power and the clipping-envelope baseline.

Scope: this falsifies the tested construction, not finite-variance confidence sequences in general.
