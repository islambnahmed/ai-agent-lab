# Keystone: decision-cost phase diagram

## Question
When does evidence-budget routing add decision value rather than merely detection machinery?

## Protocol
Seeded Monte Carlo, 5,000 runs per cell. Bernoulli baseline p=0.9 for 100 observations, then abrupt q in {0.1,0.3,0.5,0.7} for 100 observations.

Three policies share the same observations:
- alarm: frozen p=0.9 until a prequential EWMA evidence alarm (fast alpha=0.3, threshold h=6), then acts from the fast estimate;
- adapt: slow EWMA alpha=0.03;
- router: acts from fast EWMA when log(50)/KL(fast||0.9) <= 20, otherwise from slow EWMA.

Decision loss:
- risky action costs C on failure and 0 on success;
- safe action costs s;
- each policy chooses risky iff C*(1-p_hat) < s.
Regret is cumulative realized action loss minus the oracle expected loss under the true p.

Grid: q x C x s = 4 x 4 x 3 = 48 cells, C in {2,4,8,16}, s in {0.2,0.5,1.0}.

## Result
Winner counts across the 48 cells:
- router: 22
- alarm: 14
- adapt: 12

Representative router wins:
- q=0.1, C=2, s=0.2: alarm 8.974, adapt 1.450, router 1.288
- q=0.1, C=4, s=1.0: alarm 14.645, adapt 19.203, router 8.186
- q=0.3, C=4, s=1.0: alarm 18.094, adapt 18.453, router 9.013
- q=0.5, C=4, s=1.0: alarm 27.224, adapt 16.852, router 11.041

Some nominal router wins are tiny (for example q=0.7, C=16, s=1.0: 10.307 vs adapt 10.310) and should not be interpreted as meaningful without confidence intervals.

## Interpretation
The router is not universally superior, but its advantage is no longer an artifact of one hand-picked asymmetric-cost example. It wins a plurality of a coarse cost/regime grid, and its strongest gains occur where the action threshold makes both delayed reaction and overreaction costly.

The deeper lesson is that the relevant object is not a detector phase diagram alone. It is a joint **information x decision-boundary** diagram. If every plausible estimate selects the same action, better change detection has little decision value. Routing matters when uncertainty about the regime can flip the optimal action and the two error directions have materially different costs.

## Falsification / next step
Do not tune the 20-observation cutoff on this grid yet. First:
1. add bootstrap confidence intervals for pairwise regret differences;
2. add no-change cells to price false reactions explicitly;
3. normalize each cell by oracle action gap so scale changes in C do not masquerade as architectural gains;
4. then test whether a cost-aware router that uses expected value of information can dominate the fixed evidence-horizon cutoff.

This checkpoint is intentionally a boundary map, not a claim of universal superiority.
