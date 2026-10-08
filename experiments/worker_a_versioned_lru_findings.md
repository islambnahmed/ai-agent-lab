# Worker A — versioned bounded-memory route certificates (2026-10-08)

## Hypothesis
Reusing exact reverse shortest-path potentials saves compute when target locality exceeds cache capacity; bounded LRU should degrade safely when it does not. A graph update must invalidate the entire old potential cache (or prove unaffectedness) to prevent stale false certificates.

## Method
24x24 directed positive-weight grid (576 vertices), deterministic seeds: grid=90123, query generator=90234+number of distinct targets, mutation RNG=90345. 192 route queries per scenario. Dijkstra fresh per query is baseline. Cached method computes reverse Dijkstra on miss, stores a distance-to-target array in LRU of capacity 2, 8, 32, or unlimited, then follows equality edges to reconstruct a shortest path. Every graph mutation clears cached arrays and rebuilds reverse adjacency on next miss. Timings include cache lookup, misses, reverse adjacency rebuilding, invalidation, and path extraction; exclude grid and query generation. Seven repetitions with randomized method order, median wall-clock milliseconds. Python stdlib, single local CPU, synthetic data. Independent Bellman-Ford comparisons: 420 cases across capacities and graph mutations, all passed.

## Results
| distinct targets | update period | fresh ms | cache cap 2 ms | cap 8 ms | cap 32 ms | unlimited ms |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | none | 33.87 | 2.05 | 2.32 | 2.01 | 2.33 |
| 8 | none | 35.11 | 80.68 | 4.93 | 4.80 | 4.67 |
| 32 | none | 36.62 | 82.01 | 74.44 | 14.83 | 14.44 |
| 8 | every 48 | 36.34 | 80.24 | 13.77 | 14.60 | 14.06 |
| 32 | every 48 | 37.34 | 79.74 | 75.65 | 50.20 | 51.83 |
| 8 | every 12 | 37.11 | 87.30 | 55.72 | 58.41 | 59.10 |

Cache miss counts: for 8 distinct, no updates, cap2 misses 192/192, cap8 misses 8/192; with updates every 12, cap8 misses 128/192. For 32 distinct with updates every 48, cap32 misses 128/192. Each potential is 576 Python distance entries; actual memory bytes not measured.

## Findings and failure cases
* High locality: 2-target, cap2 ~16.5x faster than fresh; 8-target, cap8 ~7.1x faster.
* Cyclic thrashing: 8-target, cap2 ~2.3x slower than fresh; 32-target, cap8 ~2.0x slower.
* Update churn: 8-target, cap8, updates every 12 ~1.5x slower than fresh despite sufficient nominal cache capacity.
* **Correctness boundary**: cached equality-path reconstruction alone is not a valid proof after graph mutation. Old potentials must be invalidated (or reverified globally against the new graph). The versioned implementation passed independent Bellman-Ford tests, but only for sampled cases.

## Interpretation
Cache capacity and invalidation frequency must be included in any small-device performance claim. Caching is not automatically a win; an admission policy or compute-budget guard may help avoid thrashing. A strict version key is necessary to avoid falsely certifying paths using stale potentials. No claims about LLMs, mobile power, or general AI.

## Reproduce
Local executable artifact: worker_a_versioned_lru.py (stdlib). Uses make_grid, dijkstra, path_via_potential and bellman_ford from worker_a_route_cache_transfer.py. Run `python worker_a_versioned_lru.py` beside that file. The script ran successfully in this cycle; the source itself is not included in this commit. Next: add cache-admission gate, evaluate cost vs fresh across cyclic/skewed workloads, and measure memory bytes.
