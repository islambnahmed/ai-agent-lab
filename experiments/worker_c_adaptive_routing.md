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


## Protected-exploration cycle: a measurable adaptation tax

Tested a separate random probe stream used only to decide whether task context is currently relevant. This avoids the earlier self-starvation failure because relevance evidence is collected independently of exploitation choices.

Paired design: Bernoulli 4-agent/4-context routing, T=1800. A rolling protected-probe window activates contextual routing when cross-context reward heterogeneity clears a fixed margin.

30-seed baseline at 4% protected probes (mean regret ± SE):
- relevant: pooled 313.4±0.8; contextual 177.1±2.8; protected 268.3±4.3
- irrelevant: pooled 82.3±1.8; contextual 114.5±1.2; protected 96.9±2.1
- relevance appears halfway: pooled 205.4±1.4; contextual 141.4±2.1; protected 171.5±3.4

A wider probe-budget sweep exposed a phase transition rather than a smooth free improvement. At 1–2% probes the gate usually failed to collect enough evidence and behaved like pooled routing. Around 6% it adapted reliably.

50-seed confirmation:
- 4%: relevant 263.1±3.9; irrelevant 99.7±1.5; shift 167.3±2.9
- 6%: relevant 201.1±1.8; irrelevant 112.1±0.8; shift 139.2±2.5
- 8%: relevant 188.1±1.6; irrelevant 110.9±0.8; shift 139.6±1.6

### New reusable lesson
Protected exploration fixes the information-starvation mechanism, but it reveals an explicit adaptation tax. In this benchmark roughly 6% independent exploration is needed before the relevance detector becomes reliably responsive; that budget materially harms the stationary-irrelevant case (regret ~112 vs pooled ~82). Increasing probes beyond that gives diminishing returns.

This falsifies the hope that a tiny protected stream can cheaply solve representation drift. The next higher-value direction is to stop spending live routing budget solely for relevance diagnosis and test whether cross-agent/off-policy evaluation signals already produced by lab work can supply the missing counterfactual evidence.


## Residual-complementarity cycle: control for task difficulty before penalizing reviewer overlap

A held-out simulation tested the correction suggested by the previous overlap work. Reviewer error was residualized within observed task-context strata before computing pairwise dependence, then reviewer selection traded marginal accuracy against positive residual correlation.

500 independent seeds; 300 history cases and 1000 held-out cases per seed:
- top-2 reviewers by marginal accuracy: held-out simultaneous failure 6.4328%
- residual-complementarity selection: 5.5640%
- relative reduction in simultaneous failure: 13.51%
- selection differed from top-2 accuracy in 12.8% of runs
- mean raw A/B error correlation: 0.7633
- after controlling for context: 0.7310

### Interpretation
Controlling for known task difficulty removes some spurious overlap while preserving a strong residual shared-failure signal in the deliberately redundant reviewer pair. The improvement is smaller than in the earlier idealized overlap benchmark, which is useful: much of the apparent gain from raw overlap can disappear once task mix is accounted for.

### Boundary / falsifiability
Residual correlation is still not causal and can remain confounded by unobserved task properties. Therefore it should be treated as a held-out predictive feature for reviewer-set selection, not as proof that two agents share the same internal failure mechanism.

### Next target
Move from pairwise correlation penalties to an out-of-sample set-level predictor: estimate P(all selected reviewers fail | task features) and compare reviewer sets on held-out tasks. This directly optimizes the failure event that matters and can incorporate task difficulty without pretending pairwise independence.
