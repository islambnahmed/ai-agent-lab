# Khepri Experiment 54 — Broad log-grid adaptation

Question: can a broader effect-scale mixture remove the hard blind spots seen outside [0.01,1] without requiring a continuous prior?

Setup: quadratic e-process with V=1, alpha=.05, deterministic alternative X=d. Oracle component uses b=d^2/(1+d^2), a=2d/(1+d^2). Mixture uses equal weights on 11 log-spaced scales 1e-4, 10^-3.5, ..., 10^1.

Result (mixture/oracle hitting-time ratio):
- d=.003: 1.768
- .005: 2.057
- .008: 1.849
- .01: 1.765
- .03: 1.764
- .1: 1.758
- .3: 1.771
- 1: 1.600
- 2: 1.500
- 5: 2.000

Counterexample to the prior hypothesis: a continuous/heavy-tailed prior is not necessary merely to remove the earlier finite-range blind spot. A coarse, much broader log-grid already restores finite detection across the tested range. Denser grids (21 or 41 components over the same support) did not improve worst-case overhead; they typically raised the small-effect ratio to about 1.87-1.88 because equal prior mass per component shrinks.

Reusable lesson: support coverage and prior dilution trade off. Adding components can hurt adaptation even when approximation to the oracle scale improves. Optimize grid spacing and weights jointly, not resolution alone.

Limit: this is deterministic-alternative evidence, not a universal stochastic minimax result.
