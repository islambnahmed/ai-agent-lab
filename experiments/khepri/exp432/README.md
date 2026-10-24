# Khepri exp432 — dependency-aware repair of budgeted test plans

**2026-10-25 · AI Agent Lab · offline, synthetic, standard-library-only.**

## Question

Exp431's marginal-coverage greedy heuristic still got stuck on feasible but suboptimal selections. Can a small reversible search improve its quality under the same budget and prerequisite DAG, and how far does that transfer between SEO and gold-data test portfolios?

## Method

`repair.py` builds on exp431's `Planner` and adds: (1) greedy refill from a feasible partial plan; (2) **tabu drop**: remove selected tasks and all their dependents, temporarily forbid the dropped tasks, then refill; (3) optional single-task prerequisite-bundle seeds; and (4) best-improvement 1- or 2-drop rounds. Every candidate is validated through `Planner.plan`. Accept only higher coverage value, or equal value at lower cost. The procedure **plans checks but never executes them**.

An initial implementation was falsified by the exp431 trap (greedy value 10 vs oracle 12): dropping the bad task and immediately allowing it back made repair a no-op. Forbidding dropped tasks during refill fixed the counterexample; this failure is retained as a regression test.

## Reproduce

Run from this directory:

```bash
python -W error::ResourceWarning -m unittest -v test_repair.py
python benchmark.py > results.json
```

`planner.py` and `source_benchmark.py` are copied unmodified from exp431 for standalone reproduction. `results.json` is deterministic from 500 generated cases per domain; `scale.json` summarizes an additional 50 seeded larger instances each (20 and 30 tasks) measured on a single local machine, not a portable performance guarantee. `counterexamples.json` contains exact-oracle counterexamples to the strongest heuristic.

## Results: 500 synthetic cases per domain (new seeds 432000..432499 and 532000..532499)

| Domain | Baseline greedy matches exact | 1-drop matches | Seeded 1-drop matches | Seeded 2-drop matches | Mean coverage: baseline → seeded 2-drop |
|---|---:|---:|---:|---:|---:|
| SEO | 442/500 | 481/500 | 497/500 | **499/500** | 81.508 → **82.428** (exact 82.430) |
| Gold | 401/500 | 457/500 | 497/500 | **498/500** | 99.668 → **101.610** (exact 101.630) |

All repaired variants were at least as good as the marginal greedy baseline on these cases; seeded 2-drop strictly improved coverage in 57/500 SEO and 98/500 gold cases. The 300 additional randomized property cases passed feasibility, topological ordering, nondegradation, and oracle-bound checks. **11/11 tests passed.**

## Counterexamples / limits

- **Local optima persist.** SEO seed 432177: seeded 2-drop value 72, exact 73. Gold seed 532441: seeded 2-drop value 86, exact 89. The full inputs are in `counterexamples.json`. Local repair is not exact optimization.
- **Unknown or incorrect risk weights, costs, or coverage invalidate the decision quality.** Better search cannot repair incorrect inputs, as exp431 already demonstrated.
- **Cost of search grows.** On 50 synthetic instances each, seeded 2-drop mean local runtimes were about 3.03 ms for 20 tasks and 6.24 ms for 30 tasks; hardware/runtime dependent. No exact comparison beyond 18 tasks.
- **Model scope:** nonnegative additive risk weights, deterministic integer costs, binary known coverage, DAG prerequisites, no interactions or external side effects. No inference about real-world SEO or gold trading performance.

## Transferable lesson

When greedy planning is trapped by a bad early choice, **removal alone is insufficient if refill can immediately reselect it**. Explicitly ban the removed choice for the candidate neighborhood, drop dependent tasks as well, and check every candidate against a feasible oracle on small instances. Seeded local repair closes most measured synthetic gaps cheaply, but cannot certify optimality.
