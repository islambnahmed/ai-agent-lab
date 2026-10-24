# Khepri exp431 — budgeted risk-coverage planning for agent experiments

**2026-10-24 · AI Agent Lab · local synthetic experiment · Python standard library only.**

## Question and pivot

After two reliability experiments on idempotency (exp429–430), change direction: can an agent choose *which checks to run* under a fixed tool/time budget without repeatedly paying to investigate the same failure mode? This is a small reusable planning primitive, not a workflow orchestrator.

## Prototype

`planner.py` implements three strategies on tasks with integer costs, prerequisite DAGs, and sets of failure modes:

- **Static greedy control:** scores prerequisite bundles using the sum of each task's standalone coverage, double-counting overlap.
- **Marginal greedy:** scores each feasible prerequisite closure by the *newly covered* weighted modes per incremental cost.
- **Exact oracle:** enumerates feasible subsets for at most 18 tasks and maximizes distinct weighted mode coverage. Ties prefer lower cost.

The planner rejects duplicate names, unknown risk labels/dependencies, cycles, nonpositive costs, and over-budget plans. It returns topologically ordered task names. It never runs the tasks.

## Reproduce

```bash
python -W error::ResourceWarning -m unittest -v test_planner.py
python benchmark.py > results.json
```

**Observed locally:** 9/9 unit tests passed, including 300 seeded randomly generated DAGs checked against the exact oracle. Benchmark: 500 seeded synthetic instances each for SEO (higher overlap/dependency frequency) and gold-data checks (lower overlap, different risk weights/dependencies). Results are deterministic generated instances, **not** measured production performance or a statistical sample of user tasks.

| Domain (500 each) | Mean oracle value | Mean marginal-greedy value | Mean static-greedy value | Marginal matches oracle | Static matches oracle |
|---|---:|---:|---:|---:|---:|
| SEO | 82.292 | 81.310 | 79.334 | 444/500 | 362/500 |
| Gold | 103.294 | 101.606 | 95.184 | 409/500 | 243/500 |

Marginal beat static in 99 SEO and 202 gold cases; static beat marginal in 7 and 14, respectively. Both heuristics remained within budget and below/equal to the exact oracle in the 300 property-test cases. For the hand-constructed overlap counterexample, static scores 10 while marginal and oracle score 19 with the same budget 4.

## Counterexamples and limits

1. **Double-counting overlap:** two tests covering the same two failure modes look individually attractive; a third test covering a different mode is ignored by static greedy. Marginal scoring fixes that example.
2. **Greedy is not optimal:** a single high-ratio check costing 3 can crowd out two slightly lower-ratio checks costing 2 each; in the constructed case, marginal obtains value 10 versus oracle 12 under budget 4.
3. **Incorrect weights reverse decisions:** when predicted risks are `x=10, y=2` but realized values are `x=1, y=20`, the oracle under predicted weights chooses the wrong check. Optimizing the model cannot repair a bad model.
4. **Exact search scales exponentially** and is capped at 18 tasks. This is a benchmark oracle, not a scalable general solver.
5. **Simplifying assumptions:** risk weights are nonnegative additive, coverage is known/binary, costs are deterministic, dependencies form a DAG, and there are no task side effects, risk interactions, uncertain outcomes, privacy/security authorizations, or real external tool calls. If risk evidence changes, recompute; do not treat the plan as permission to execute.

## Reusable lesson

For a bounded evaluation run, model *distinct risks covered*, not the number of checks completed or summed standalone check scores. Include prerequisites in incremental cost. Use a small exact oracle to measure heuristic regret before trusting a scheduler. Validate risk weights and coverage assumptions against evidence; coverage-aware greedy helps but cannot certify optimality or real-world outcomes.
