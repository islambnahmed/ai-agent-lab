# Experiment 30 — Four-mode pairwise independence can hide a 1/6 joint-failure risk

## Question

For four binary failure indicators with P(X_i=1)=1/2 and P(X_i=X_j=1)=1/4 for every distinct pair, how large can P(X_1=X_2=X_3=X_4=1) be?

Every pair is independent, but mutual independence is **not** implied.

## Sharp result

The exact feasible interval for all four modes failing is **[0, 1/6]**. Equivalently, P(at least one survives) lies in **[5/6, 1]**. A fully independent four-mode model gives joint failure 1/16 and survival 15/16, only one admissible point.

### Witness for the lower endpoint

Sample uniformly from the eight four-bit strings of **odd parity** (Hamming weight 1 or 3). Each bit is 1 in four of eight states, each pair is 1 in two of eight, and 1111 is impossible. Hence all specified moments hold but P(all fail)=0.

### Witness for the upper endpoint

Let S be the number of failing modes. Sample S=4 with probability 1/6, S=2 with probability 1/2, and S=1 with probability 1/3. Conditional on S, sample uniformly among the four-bit states with exactly S ones.

By exchangeability, each marginal is E[S]/4 = (4/6+2/2+1/3)/4 = 1/2. Each pairwise joint is E[S(S-1)]/(4*3) = (12/6+2/2)/12 = 1/4. Yet P(all fail)=P(S=4)=1/6.

### Proof no higher value is possible

For integer S in {0,1,2,3,4}, (S-1)(S-2) is nonnegative, and equals 6 when S=4. Therefore:

    6 P(S=4) <= E[(S-1)(S-2)]
                = E[S(S-1)] - 2 E[S] + 2
                = 3 - 4 + 2 = 1.

Thus P(all fail) <= 1/6. The two witnesses establish both endpoints; convex mixtures establish the entire interval.

## Decision implication

A policy requiring at least 90% probability that one evidence path survives would pass under an unjustified full-independence point estimate (93.75%), but **cannot** be certified from marginals and pairwise independence alone: worst-case survival is 83.33%.

## Reproduction

Run `python tools/dependence_bounds.py`. The built-in regression asserts the four-mode bounds and rejects an infeasible four-mode cyclic constraint set. `.github/workflows/ci.yml` now executes this regression on each push and pull request.

This is a synthetic mathematical counterexample, not an empirical reliability estimate. The exact solver enumerates vertices for cyclic graphs of at most four modes; forest graphs use a separate exact fast path.
