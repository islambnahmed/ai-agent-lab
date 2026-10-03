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
