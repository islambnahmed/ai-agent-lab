# Experiment 42 — Why finite variance alone cannot give a useful finite-sample mean boundary

## Question
After Experiment 41 falsified naive Studentization, can we replace it with a genuinely distribution-free finite-variance sequential mean test without assuming a known variance bound?

## Construction
Use the same rare-compensating family:
- X = 1 with probability 1-p
- X = -(1-p)/p with probability p
- E[X] = 0 and Var(X) = (1-p)/p, finite for every p>0.

For any finite horizon N and any desired indistinguishability level delta, choose p <= delta/N. Then with probability
(1-p)^N >= 1-Np >= 1-delta,
the entire observed prefix is exactly (1,1,...,1).

That same prefix is also produced with probability 1 by the alternative distribution X=1, whose mean is +1 and variance is 0.

## Counterexample / implication
Any procedure that, from only the first N samples and the assumption "variance is finite", confidently certifies positive mean on the all-ones prefix will make the same certification under a mean-zero finite-variance distribution with probability at least 1-delta, by choosing p small enough.

Since delta can be arbitrarily small, no nontrivial finite-sample distribution-free lower confidence bound for the mean can be both:
1. uniformly valid over *all* finite-variance distributions with no quantitative scale bound, and
2. positive on the deterministic all-ones sample.

Sequential monitoring cannot repair this identifiability problem; at any finite stopping time that accepts the all-ones alternative, a sufficiently rare compensating-outlier null mimics its entire history with arbitrarily high probability.

## Transfer
The sign-reversed construction gives the same obstruction for upper confidence bounds. The lesson also applies beyond sequential tests: robust estimators can estimate under finite variance with rates depending on the unknown variance, but an honest finite-sample confidence guarantee needs some quantitative control/estimation condition; the bare statement "variance is finite" supplies no usable finite scale.

## Model correction
Experiments 40–41 were searching too broadly. The next benchmark should not ask for a distribution-free anytime mean test under only unspecified finite variance. That target is impossible in the useful finite-sample sense above.

Viable directions must add structure, for example:
- a known upper bound on variance/second moment;
- bounded observations;
- symmetry or another tail-shape assumption;
- a robust scale condition that itself has a finite-sample guarantee;
- or asymptotic rather than finite-sample validity.

## Reusable gate
Before benchmarking a new sequential mean method, write down the quantitative assumption that makes the mean identifiable at finite sample size. If the only assumption is "some finite variance exists", reject the target before simulation.

This is an analytic counterexample, not a Monte Carlo claim.
