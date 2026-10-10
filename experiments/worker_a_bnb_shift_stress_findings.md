# Worker A — bounded BnB size/distribution shift stress (2026-10-10)

## Question
The previous 30-item heldout benchmark reported 100% accepted coverage at 512 expanded nodes in the `large_lumpy` domain. Does that coverage survive increasing item count while keeping the node budget fixed?

## Reproduction
A local test harness was executed against a faithful copy of the previously committed `worker_a_memory_bnb.py` solver, without algorithmic modifications. **The harness source was not committed: a separate attempted code upload was blocked.** The complete local script is available as `worker_a_bnb_shift_stress.py` in the cycle artifact. To reproduce, place that script alongside `experiments/worker_a_memory_bnb.py` and run `python worker_a_bnb_shift_stress.py`. Python standard library only. Four new independent seeds (88031–88034), 100 cases per seed, for each of three domains and n=30/60/120: 3,600 problems, 7,200 bounded-search decisions (128 and 512 nodes). Exact 0/1 dynamic programming provides independent ground truth **only for evaluation**. The 5% quality certificate does not inspect ground truth.

The domains: `lumpy` = item weights 25–70, values 20–120, capacity 75; `tight_capacity` = weights 25–60, values 40–120, capacity 65–100; `two_scale` = 50/50 mixture of tiny items (weights 1–3, values 1–5) and larger items (weights 30–90, values 30–150), capacity 20% of total weights.

## Heldout results (out of 400 cases per row)
| Domain | n | Root certified | Accepted, 128 nodes | Accepted, 512 nodes | Proven exact, 512 nodes |
|---|---:|---:|---:|---:|---:|
| lumpy | 30 | 31 | 333 | **400** | 400 |
| lumpy | 60 | 12 | 73 | **288** | 258 |
| lumpy | 120 | 17 | 37 | **62** | 62 |
| tight_capacity | 30 | 99 | 310 | **399** | 396 |
| tight_capacity | 60 | 98 | 175 | **284** | 262 |
| tight_capacity | 120 | 76 | 103 | **136** | 109 |
| two_scale | 30 | 278 | 304 | **330** | 255 |
| two_scale | 60 | 393 | 393 | **395** | 163 |
| two_scale | 120 | 400 | 400 | **400** | 155 |

All 7,200 decisions matched the independent DP quality/exactness conditions: zero invalid accepted results. Unaccepted cases returned `DEFER` rather than an unsupported answer. The result is not a claim about real LLM agents.

## Correction and implications
The 512-node budget's earlier **100% coverage** is not a transferable property. On independent `lumpy` tasks, it falls from **400/400 at 30 items to 62/400 (15.5%) at 120 items**. On `tight_capacity`, coverage falls from **399/400 to 136/400 (34%)**. Yet `two_scale` remains 400/400 at 120 items. The critical variable is both size **and** structure; item count alone is an inadequate difficulty predictor.

A 512-expanded-node budget bounds only one part of computational work. It is not a hard latency, energy, or RSS cap: sorting, upper-bound scans, and Python allocation costs grow with n. A fixed budget is safe for correctness because of honest deferral, but not reliable for task completion.

## Next experiment
Compare a **cheap root certificate → bounded search → honest DEFER** cascade against an *observable* work budget (count bound-scanned items, not only expanded nodes) and a size-aware budget. Report acceptance, p95 latency, peak process RSS, and failure cases under heldout size/structure shift. If extra routing overhead erases gains, use the simpler method.

## Limitations
Synthetic positive-integer knapsack instances; fixed seeds; 400 cases per setting; no real-agent task; no phone/device measurements. Timing was measured locally but intentionally omitted here because sub-millisecond p95 Python wall-clock values are machine-dependent and noisy. No claims of device-level speed or energy savings.
