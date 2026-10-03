# Worker C contextual routing benchmark

Question: can task context reduce partial-feedback cost without over-fragmenting evidence?

Simulation: 4 task types, 4 agents, T=2500. Each task type had a different best agent.

Across 20 seeds, mean regret:
- global/no-context: about 419
- perfect context: about 227
- 15% corrupted context labels: about 285
- 35% corrupted labels: about 336
- 60% corrupted labels: about 391

The paired contextual-minus-global improvement at 60% corruption was about -30 regret (paired SE about 2.6).

Counterexample: context was irrelevant and the same agent was best for every task type. Across 30 seeds, global regret was about 102.8 while contextual regret was about 229.5. Context splitting cost about 126.7 regret (paired SE about 3.7).

## Reusable design rule
Context is a hypothesis, not automatically a routing feature. Pool evidence globally unless context shows predictive value for relative agent performance. Split by context only when expected specialization gain exceeds the sample-fragmentation cost.

Next target: build and falsify a relevance gate that decides when to pool versus split evidence.
