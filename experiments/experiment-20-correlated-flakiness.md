# Experiment 20 — Correlated flakiness breaks repeated voting

## Question
Experiment 19 showed that seven-vote confirmation greatly improves failure minimization when observation errors are independent. Does that lesson survive correlated errors?

## Setup
Same synthetic debugging task as Experiment 19: 10 components with a hidden 2-component true cause; deletion minimization must recover that exact pair. Base observation flip probability is 5%, seven-vote majority with early stopping, 5,000 randomized trials per condition.

A correlation parameter controls whether the seven observations for a candidate share one latent flip:
- rho=0: all vote errors independent.
- rho=1: all seven votes share the same error state.
- intermediate rho: with probability rho, a candidate's seven observations share one latent flip; otherwise their flips are independent.

Fixed experiment seed.

## Results

| within-candidate correlation rho | exact cause recovered | mean test calls |
|---:|---:|---:|
| 0.00 | 99.74% | 46.27 |
| 0.10 | 94.64% | 45.95 |
| 0.25 | 87.12% | 45.19 |
| 0.50 | 75.56% | 44.13 |
| 0.75 | 65.04% | 43.16 |
| 1.00 | 57.02% | 42.00 |

The apparent reduction in calls at high correlation is not an improvement: correlated votes rapidly agree on the same wrong observation.

## Competing mitigation: separate the observations
A second 5,000-trial comparison at 5% error used two extremes:
- seven votes from one fully shared error state: 56.62% recovery, 41.94 mean calls;
- seven independently refreshed error states: 99.86% recovery, 46.33 mean calls.

This synthetic model makes the mechanism explicit: repetition only buys confidence to the extent that repetitions contain fresh information.

## Counterexample / correction
Experiment 19's "repeat the test seven times" lesson is incomplete. Seven executions are not seven independent pieces of evidence when they share environment, cached state, timing window, dependency outage, seed, worker, or another common cause. Majority voting can become confidently wrong.

## Transferable lesson
Count independent failure opportunities, not raw repetitions. For flaky debugging, diversity/separation across likely common causes can be more valuable than simply increasing the number of immediate reruns.

Possible practical dimensions include fresh process/environment, time separation, different worker, cleared state, or changed seed when those changes are valid for the system under test. This experiment does not claim any one mechanism is universally appropriate.

## Scope
The benchmark is synthetic and deliberately simple. Correlation here is modeled as a shared latent flip within a candidate evaluation. Real systems can have longer bursts, asymmetric errors, stateful transitions, and nonstationarity. The result establishes a counterexample to naive majority-vote confidence, not a universal production-noise model.
