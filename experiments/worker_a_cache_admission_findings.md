# Worker A — cache admission beats thrashing, not universally (2026-10-08)

## Decision
Test an **admission gate** rather than treating LRU as automatically beneficial. A small exact route agent should spend memory only on targets whose observed reuse distance fits the cache, and avoid reverse shortest-path computations for targets that are unlikely to recur before eviction.

## Method
Independent local Python stdlib script `worker_a_cache_admission.py` using the existing `worker_a_route_cache_transfer.py` and `worker_a_versioned_lru.py`. Directed positive-weight 24×24 grid, 192 queries per scenario, capacity 2/8/32 target potentials. Paired randomized method order, 7 repetitions, median wall-clock ms. Each graph mutation clears both cache and target-history, preventing stale proofs. Compared (1) fresh source Dijkstra every query, (2) LRU reverse-Dijkstra potential per target miss, (3) a bounded **three-touch admission** gate. The gate tracks at most `capacity` recent distinct targets and admits only after three observations within that reuse-distance window; before admission it computes the fresh answer. This is a deliberately simple baseline, not an optimized predictor. **2,340 individual decisions** independently matched Bellman-Ford across graph mutations, capacities and policies.

## Measurements
| Scenario | Capacity | Fresh ms | LRU ms | Three-touch ms | Gate reverse builds | LRU reverse builds |
|---|---:|---:|---:|---:|---:|---:|
| 2 cyclic targets, static | 2 | 36.07 | 2.61 | 3.51 | 2 | 2 |
| 8 cyclic targets, static | 2 | 33.99 | 73.05 | 35.84 | 0 | 192 |
| 8 cyclic targets, static | 8 | 39.93 | 8.98 | 10.28 | 8 | 8 |
| 32 cyclic targets, static | 8 | 44.74 | 82.83 | 42.77 | 0 | 192 |
| 32 cyclic targets, static | 32 | 52.26 | 50.87 | 76.97 | 32 | 32 |
| 8 cyclic targets, update/48 | 8 | 52.81 | 22.05 | 43.96 | 32 | 32 |
| 8 cyclic targets, update/12 | 8 | 45.43 | 81.52 | 49.33 | 0 | 128 |
| 32 cyclic targets, update/48 | 32 | 56.19 | 186.90 | 55.32 | 0 | 128 |
| 32 targets, 80% hot, static | 8 | 74.35 | 30.67 | 20.31 | 2 | 34 |

All times include policy decisions, cache operations, graph-version invalidation, route reconstruction and computations, but not graph/query generation. Memory payload estimates at peak: 2 potentials ~41,584 bytes; 8 ~166,336; 32 ~665,344. These are Python object estimates, **not RSS**, and exclude graph and history overhead.

## Key findings
- **Clear anti-thrashing result**: with 8 cyclic targets and capacity 2, LRU spent 73.05 ms and rebuilt potentials 192 times; gate avoided all reverse builds and finished in 35.84 ms (close to fresh 33.99 ms).
- **Update churn**: 32 targets, capacity 32, graph update every 48 queries: LRU 186.90 ms vs gate 55.32 ms and fresh 56.19 ms. History resets on graph version changes, so the gate does not admit targets without enough reuse.
- **Skewed workloads**: 80% hot target, capacity 8: gate 20.31 ms vs LRU 30.67 ms, with 2 vs 34 reverse builds.
- **Important counterexample**: 32 cyclic targets, capacity 32, static graph: gate 76.97 ms vs LRU 50.87 ms and fresh 52.26 ms. A three-touch gate delays profitable reuse; no single admission rule wins all cases.
- Correctness checked against Bellman-Ford, but only on finite synthetic tests. A graph-version change **must invalidate cached potentials**; admission does not replace version safety.

## Next high-value test
Compare 2-touch, 3-touch, and an online **cost-aware** gate on unseen bursty/phase-changing streams, measuring total CPU time, memory, and cache accuracy with randomized ordering. Avoid optimizing only one cyclic workload. Consider cache-free fallback when a version is expected to expire before amortization, but never use future knowledge unavailable at runtime.

## Reproduction and status
Local reproducible artifact: `/mnt/data/worker_a_cache_admission.py`; imports the two earlier local files listed above. This report records an executed local experiment. Source-file upload is not implied by the report.