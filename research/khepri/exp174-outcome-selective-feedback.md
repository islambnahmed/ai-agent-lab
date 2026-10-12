# Khepri experiment 174 — outcome-selective delayed feedback

Date: 2026-10-12. Synthetic-only lab research; no live agent or gold-site changes.

## Question
Exp173 assumed each task type had a fixed feedback delay. What if successes arrive more slowly than failures (or vice versa)? The currently visible outcomes are then a biased subset of launched tasks.

## Tested mechanism
Three-arm 240-decision synthetic bandit. Compare ordinary UCB, pending-count UCB, cohort-complete UCB (withhold even early feedback until the arm-specific *known maximum delay*), cohort+pending UCB, and round-robin. 500 independent random seeds per case, plus 500 fresh replication seeds; same potential outcomes across policies within seed; oracle probabilities used only for regret scoring. Paired 95% normal-approximation intervals across seeds.

## Results (pseudo-regret reduction vs ordinary UCB; positive = improvement)

| Scenario | Pending-aware, initial | Cohort, initial | Cohort, fresh seeds |
|---|---:|---:|---:|
| Gold-like best arm's successes slow | -1.420 [-1.834,-1.007] | +1.817 [1.419,2.216] | +1.248 [0.875,1.622] |
| Gold-like bad arm's successes fast | +1.495 [0.950,2.039] | +1.010 [0.587,1.433] | +1.283 [0.872,1.695] |
| Gold-like best arm's successes fast | +0.125 [-0.221,0.472] | -0.045 [-0.376,0.286] | -0.356 [-0.705,-0.007] |
| SEO-like best arm's successes slow | -0.586 [-0.773,-0.399] | +1.257 [1.047,1.466] | +1.210 [1.004,1.417] |
| SEO-like bad arm's successes fast | +1.643 [1.283,2.003] | +1.192 [0.870,1.513] | +0.651 [0.343,0.958] |
| SEO-like best arm's successes fast | +0.016 [-0.177,0.210] | -0.122 [-0.306,0.063] | -0.238 [-0.412,-0.063] |

Negative controls: when delays were independent of outcomes and always 36 steps, cohort UCB and UCB made exactly identical choices; likewise when all delays were one step.

Fixed-sampling audit (20,000 trials): 85% true-success arm, successes delayed 36 and failures delayed 1: at t=20 the visible feedback had 0% successes among 2,956 arrivals; at t=48 visible success was 61.10% while full eligible cohorts were 84.91%. Reversing delays for a 45%-success arm yielded 100% visible success at t=20 and 74.92% at t=48, versus 44.89% among fully eligible cohorts.

## Lesson
Delay is potentially informative about the outcome. Penalizing pending work as already explored can suppress a valuable slow-success arm. A maximum-delay cohort gate removes within-arm outcome-dependent arrival selection under its bounded-delay assumptions, but discards useful early evidence and can perform worse. No single policy dominated.

12 unit tests passed, including separate slow reference vs optimized event-queue simulator on 40 seeds x 8 scenarios x 5 policies = 1,600 full trajectory comparisons, no future-label leakage, and negative controls. Independent replication: 500 new seeds per scenario.

## Limits / next step
These are chosen synthetic worlds, not measurements of real agents or gold/SEO outcomes. Confidence intervals cover seed-to-seed simulation variation, not external validity. Known finite maximum delays are required; unknown, censored, or unbounded delays break the simple cohort rule. Before live allocation, collect task launch, outcome arrival, utility, and censoring timestamps, then pre-register a prospective comparison. No production change.
