# Worker A — capacity-pressure admission and safe direct-compute fallback (2026-10-09)

## Question
Can a small route solver avoid cache thrashing without giving up the gains of exact reusable shortest-path potentials? Test a bounded online admission rule, not a learned model.

## Algorithm
Maintain a rolling window of 32 requested destinations (Counter + deque). On a cache miss, build a reverse-Dijkstra exact potential only if: (1) the target occurred at least 3 times in the window, (2) the known edge-update interval is either absent or >=8 requests, and (3) if distinct targets in the window exceed cache capacity, the target occurs at least ceil(2 * window_length / capacity) times. Otherwise compute that request's distance directly using forward Dijkstra. Existing cache hits remain usable. On each single positive-weight edge update, retain a potential only when the previously documented local mathematical exactness test succeeds; invalidate otherwise. All data structures are bounded by window size and cache capacity. A failed admission prediction can waste computation but cannot turn a stale answer into a valid one.

This is a hand-designed rule using the workload's *known* mutation period. It is not a general learned policy. It is not guaranteed optimal. The first version omitted capacity pressure, and caused a thrashing regression.

## Reproducible experiment
Local code: `worker_a_adaptive_fallback.py`, imports `worker_a_hybrid_cache.py` (both delivered as local artifacts, **not claimed uploaded to GitHub**). Python stdlib, directed positive-weight 24x24 grid, 256 queries per case, 10 workloads (static, 4/12-update, cyclic, skewed, phase, burst, uniform, hot-flip), 3 graph/query seeds per case, 2 shuffled policy-order timing repetitions per seed, wall-clock includes admission decisions, update checks, reverse graph work and shortest-path computations. Compared fresh Dijkstra, selective LRU, selective gate-3, and adaptive variants. Results below are median milliseconds across three seeds; geomean below is over **30** case x seed trials.

| Workload | Fresh | Selective LRU | Adaptive-3 without pressure | Adaptive-3 with pressure factor 2 |
|---|---:|---:|---:|---:|
| cyclic8 static cap8 | 35.89 | **4.10** | 6.73 | 6.56 |
| cyclic8 static cap2 | 37.84 | 82.85 | 79.87 | **37.93** |
| cyclic8 update12 cap8 | 42.64 | **23.15** | 23.66 | 24.09 |
| cyclic8 update4 cap8 | 42.51 | 50.63 | **40.60** | 42.65 |
| skew32 static cap8 | 36.49 | 14.71 | 9.90 | **9.69** |
| skew32 update12 cap8 | 43.10 | 21.98 | 13.84 | **13.55** |
| phases update12 cap8 | 42.23 | **26.35** | 34.50 | 38.62 |
| bursts update12 cap8 | 40.24 | **23.38** | 39.29 | 38.08 |
| uniform64 update12 cap8 | **39.36** | 76.81 | 43.15 | 39.84 |
| hot_flip update12 cap8 | 36.62 | 19.95 | **14.11** | 14.22 |

Geometric mean elapsed/fresh across 30 case-seed trials: fresh **1.0000**, selective LRU **0.6361**, selective gate3 **0.6159**, adaptive3 **0.5911**, adaptive3+pressure1.5 **0.5580**, adaptive3+pressure2 **0.5565**. The pressure2 policy therefore took ~12.5% less geometric-mean time than selective LRU on this test set (0.5565/0.6361); it was *not* best in most individual cases.

Ablation: on cyclic8 static cap2, the naive adaptive3 built 240 reverse potentials per 256 requests, while pressure2 built **0**; measured median time fell from 79.87 to 37.93 ms. On uniform64 update12 cap8, builds dropped 16 to 0 and time from 43.15 to 39.84 ms. But on phases update12 cap8, pressure2 was slower than selective LRU (38.62 vs 26.35 ms). More complicated admission does not dominate simpler strategies.

## Verification
11,520 small-grid query results checked against independent Bellman-Ford (4x4 and 5x5, 4 seeds, 2 capacities, 3 mutation intervals, 3 adaptive policies plus pressure variants). 181 retained-potential full reverse-Dijkstra rechecks passed. All six policies' outputs agreed per 24x24 trial; no mismatches observed. These are finite tests, not proof that the admission heuristic is optimal. The cached exactness property follows the earlier local proof under strictly positive directed edge weights and single-edge weight edits.

## Caveats and next experiment
One machine, synthetic grids, Python wall-clock (no CPU/RSS/energy measurements), small number of timing repeats, known mutation interval used as input, no adaptive learning and no LLM/mobile demonstration. Future work should evaluate mutation rates not known in advance and abrupt nonstationary changes, and replace period input with a measured recent update rate. Cross-validate against graphs with varying connectivity and source/target distributions. If added controller overhead erases gains, retire it instead of further tuning on this same benchmark.
