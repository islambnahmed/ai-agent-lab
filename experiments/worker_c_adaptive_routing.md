# Worker C — Adaptive Agent Routing Benchmark

## Why this replaces the old direction
Worker C's prior branch was 83 commits behind main and contained one coordination-consistency utility. This experiment redirects Worker C toward a transferable capability: selecting agents when their task success rates change over time.

## Question
Does forgetting old performance improve routing when the best agent changes?

## Tested policies
- cumulative UCB: uses all historical outcomes.
- sliding-window UCB: estimates each agent from its recent outcomes.
- discounted UCB: exponentially forgets old outcomes.
- naive change-triggered reset: exploratory reset when recent-vs-old success differs by a threshold.

## Evidence (simulation)
Scenario A: four abrupt regimes, clearly changing best agent.
- cumulative: accuracy 0.7944, regret 106.15
- sliding window: accuracy 0.81335, regret 68.30
- discounted: accuracy 0.73488, regret 225.24
Sliding-window regret was ~35.7% lower than cumulative.

Scenario B: five regimes with closer agent success rates.
- cumulative: accuracy 0.73956, regret 80.875
- sliding window: accuracy 0.74054, regret 78.913
- discounted: accuracy 0.72834, regret 103.325
The sliding-window advantage nearly vanished.

Independent counterexample test:
- abrupt: cumulative regret 112.72; window 75.41; naive reset 126.18
- close regimes: cumulative 77.13; window 88.83; naive reset 94.07
The naive change-triggered reset was worse, and the window policy can also lose when regimes are subtle.

## Durable lesson
Adaptive routing should not assume one forgetting rule is universally best. First infer whether observed performance is stationary, abruptly shifting, or too noisy to distinguish; then choose the memory horizon/routing policy. A naive reset detector can amplify noise and worsen regret.

## Next falsifiable target
Build a meta-router that selects between cumulative and recent-window evidence using an online held-out score, then test whether its regret stays close to the better policy in both abrupt and subtle-shift environments.

No claim is made that these synthetic results transfer to real agents until tested on real lab task outcomes.


## Meta-router falsification cycle
A direct meta-router that chose cumulative vs recent-window estimates from its own prediction loss did not stay close to the better base policy.

Mean regret over 10 seeds (T=1200):
- abrupt: cumulative 83.16, window 58.23, meta 70.34
- subtle: cumulative 44.85, window 40.69, meta 43.50
- stationary: cumulative 58.77, window 69.37, meta 63.98

An EXP3-style policy competition layer also failed to close the gap (abrupt regret roughly 74.9–77.5 across tested block sizes). A dedicated random probe stream removed some selection bias but paid too much sample cost: with 4% probes, abrupt regret rose to 104.09.

### Important correction
The bottleneck is not merely choosing a change-detection threshold. In bandit routing, the router only observes outcomes for agents it selects. Therefore change diagnosis and policy comparison are themselves partial-information problems. A detector built from selected outcomes has feedback/selection bias; unbiased probes consume routing budget and can react too slowly to abrupt shifts.

### Design consequence
Do not promote a generic "detect drift then reset/switch" meta-router yet. The next architecture should exploit task context or naturally available cross-agent evaluation signals, or use a principled nonstationary-bandit method with an explicit dynamic-regret target. Synthetic reward-only routing alone cannot cheaply provide both fast change detection and low stationary cost in the tested regimes.


## Relevance-gate cycle: context must earn its complexity

A new relevance gate was tested before allowing task context to split the router's evidence. It compares context-specific vs pooled agent success estimates and only activates contextual UCB when the observed heterogeneity clears an uncertainty margin.

20 paired seeds, T=2500:
- strongly relevant context: pooled regret 539.9 ±1.4 SE; contextual 236.2 ±2.7; gate 232.2 ±2.9
- irrelevant context: pooled 116.8 ±3.1; contextual 170.9 ±2.0; gate 118.4 ±3.6
- weakly relevant context: pooled 147.8 ±1.1; contextual 126.3 ±1.6; gate 135.8 ±2.4
- environment shifts halfway from irrelevant to strongly relevant: pooled 340.9 ±2.2; contextual 198.2 ±3.4; gate 292.6 ±7.1

This is a useful partial success: the gate nearly matches the correct choice at both static extremes and captures part of weak context value. But it fails badly when relevance itself changes over time.

A competing fix—periodically resetting only the gate's relevance evidence—was falsified. With epoch sizes 250/500/1000 it preserved stationary irrelevant performance (~117–118 regret) but harmed relevant performance (493.9/378.8/305.3) and did not solve the shift case (329.6/297.3/293.1).

### Reusable lesson
There are two adaptation problems, not one: which agent is best, and whether the feature/context representation is currently useful. A relevance gate trained only from actions selected by the same router can self-starve the evidence needed to discover a newly useful context. Blind periodic resets worsen this by repeatedly discarding hard-won relevance evidence.

### Next target
Stop threshold tuning. Test a small protected exploration budget specifically for representation/relevance learning, separated from exploitation, and measure the dynamic-regret cost. If that remains too expensive, pivot to offline/cross-agent evaluation signals rather than reward-only online routing.
