# Khepri exp403 — Failure-domain-aware planning for redundant AI tools

## Self-directed question
Can an AI agent choose a cheaper-but-shared or costlier-but-diverse set of read-only data tools without confusing *multiple endpoints* with *independent failure domains*? This is a deliberate pivot from exp393–402's data validation and idempotency work toward **decision-making under correlated tool failure**.

## Model and reusable capability
`planner.py` enumerates failure-domain outage states and computes the exact probability that every workflow stage succeeds. Each stage may have parallel OR-redundant tools; stages compose with AND. Each failure domain has one latent outage event per run. Conditional on those events, tool invocations are independent. Each tool has healthy/outage conditional success probabilities and a fixed invocation cost. The planner selects the plan with the highest `reward * P(success) - fixed_cost`. `naive_success` is an intentionally incorrect comparator which treats marginal tool successes as independent. No network calls or external side effects.

## Falsifying example
Two cheap replicas from one shared domain: healthy success .99, outage success .02, shared outage probability .18, cost .4 each. Two more expensive replicas from separate domains: healthy .96, outage .25, outage probability .08 each, cost 1.0 each. Reward=10. The naive estimate gives the shared pair **96.5923%** success, while exact enumeration gives **82.7046%**. The diverse pair has **99.0630%** success. Naive planner chooses shared; exact planner chooses diverse, with modeled expected utilities **7.470460** vs **7.906298**. This is a synthetic counterexample, not an observed outage rate.

## Deterministic transfer benchmark
Seed 403; 2,000 synthetic scenarios per domain. Gold: naive disagrees with model-optimal choice in **868/2,000**, mean modeled utility regret **0.288837**, worst **1.881418**. SEO: **1,020/2,000** disagreements, mean regret **0.367594**, worst **2.006942**. Exact calculation cross-checked against Monte Carlo for 24 plan/scenario combinations per domain (30,000 runs each): maximum absolute probability differences **0.004560** (gold) and **0.003227** (SEO). **16/16** local unit tests passed. Full parameters, code and outputs in `benchmark.py` and `results.json`.

## Competing explanation and failure of the improved method
The model is only as good as its failure-domain map and outage estimates. Underestimating all outage probabilities by 50% causes wrong choices in **649/2,000 gold** and **707/2,000 SEO** synthetic scenarios, with mean true-model utility regrets **0.155710** and **0.173797** respectively. Assuming outages never happen chooses the wrong plan in the focal example. Also, correlation does **not always make naive success too optimistic**: for serial AND stages using the same outage domain, positive correlation can make the naive estimate *too pessimistic*. The direction depends on AND/OR structure.

## Reproduce
From this directory, Python 3.10+ standard library only:

```sh
python3 -m unittest -v test_planner.py
python3 benchmark.py
```

## Limits and deployment decision
All figures are synthetic; no actual gold/SEO vendor outage rates, latency, budget, fallback costs, data correctness, or live execution were measured. This planner models success as a binary event, charges all scheduled tool costs even if earlier stages fail, disallows repeated invocation IDs, and enumerates at most 16 outage domains (exponential runtime). The outage domains are independent of one another by assumption; correlated *domains*, adaptive retries, time-varying outages, and uncertain probabilities require further work. Not production-ready. Keep on a research branch; do not alter `main`.

## Practical lesson
Before adding redundant AI Agent tools, identify their *common failure domains* and test sensitivity to outage-rate estimation. Endpoint count alone is not reliability. A cheap fallback in the same failure domain can be worse than a single genuinely independent source.
