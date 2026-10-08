# Worker A — exact selective invalidation for route certificates (2026-10-09)

## Research question
Must every graph update discard every cached exact shortest-path potential? No. A **single directed positive-weight edge update** admits a cheap, local sufficient test for preserving each target's cached potential. This is not a heuristic: a retained potential is still exact for every source.

## Local proof (old exact potential p, changed edge u→v from a to b)
- If **b <= a** (decrease): retain iff `p[u] <= b + p[v]`. Every old shortest path still exists; the only changed Bellman inequality remains satisfied. Thus no new shorter path is possible and old distances remain exact.
- If **b > a** (increase): retain iff node `u` still has at least one outgoing **tight** edge `u→x` with `p[u] = new_weight(u,x) + p[x]`. All other nodes keep an old tight successor. Since weights are strictly positive, following tight successors strictly decreases p and reaches the target. Hence every old distance is still attained; increases cannot introduce shorter paths.
- Otherwise **invalidate** that target's potential and rebuild on next request. The test is conservative; it never claims that a failed test proves the potential incorrect.

## Experiment
Python stdlib, 24×24 directed grid, 256 queries per workload, cache capacity 2/8/32 target potentials, single-edge updates every 4/12/48 requests (or none). Seven repetitions with randomized policy order; median wall-clock milliseconds. All timings include update handling, local checks, reverse-graph rebuilds, shortest-path computations, and path reconstruction; graph/query generation excluded. Compared fresh per-query Dijkstra, global cache clearing, and selective invalidation. Graph seed 90123, mutation seed 90345. Small-graph independent Bellman-Ford comparisons and full cached-potential rechecks after mutation.

| Workload | Fresh ms | Global clear ms | Selective ms | Global builds | Selective builds | Retained / invalidated |
|---|---:|---:|---:|---:|---:|---:|
| 8 targets, update every 4 | 36.61 | 97.46 | 45.35 | 256 | 116 | 324 / 108 |
| 8 targets, update every 12 | 36.10 | 61.02 | **12.47** | 172 | 28 | 148 / 20 |
| 8 targets, update every 48 | 36.04 | 17.86 | **5.63** | 48 | 11 | 37 / 3 |
| 32 targets, update every 4 | **41.20** | 92.57 | 85.48 | 256 | 231 | 655 / 203 |
| 32 targets, update every 12 | 42.28 | 88.15 | **39.72** | 256 | 109 | 486 / 81 |
| 32 targets, update every 48 | 41.69 | 60.25 | **20.97** | 176 | 56 | 136 / 24 |
| 8 targets, static | 36.46 | 4.29 | 4.14 | 8 | 8 | 0 / 0 |
| 32 targets, static | 41.79 | **11.91** | 12.42 | 32 | 32 | 0 / 0 |
| 8 targets, capacity 2, update every 12 | **36.79** | 87.39 | 87.64 | 256 | 256 | 38 / 4 |

**Verification:** 52,920 query / independent Bellman-Ford comparisons passed; 17,359 full cached-potential survival rechecks passed. Zero mismatches observed in these finite tests; the local preservation argument provides the stronger mathematical guarantee under stated assumptions.

## Interpretation
- Selective invalidation cut reverse-Dijkstra builds from 172 to 28 on 8-target update/12, and time from 61.02 to 12.47 ms (~4.9× faster than global clearing). It prevents a large amount of needless work.
- It **does not solve cache thrashing**: capacity 2 vs 8 cyclic targets stayed slower than fresh (87.64 vs 36.79 ms). High mutation frequency and 32 targets also favored fresh.
- Unlike earlier blanket statements that *every* version change requires discarding the entire cache, the correct requirement is to **invalidate or prove exactness after changes**. A globally versioned cache is sufficient but unnecessarily conservative in this special case.
- Caveats: positive weights, single-edge weight mutations, no topology changes, synthetic grids, one machine, Python timings, and no measured device power/RSS. For zero-weight or negative edges the tight-edge termination proof needs modification. For batches of edits, apply tests sequentially to exact survivors or clear/recompute.

## Reproduction and next decision
Executed local source: `worker_a_selective_invalidation.py` (imports the two earlier local Worker A route modules). No source upload implied by this report. Next: combine **admission gating** with safe selective invalidation, compare against a fresh fallback on out-of-distribution bursty workloads; do not assume more caching is always better.
