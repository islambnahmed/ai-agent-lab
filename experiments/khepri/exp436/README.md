# Khepri exp436 — temporal provenance closure for joins and derived features

**2026-10-25 | offline synthetic experiment | Python stdlib only**

## Question

Does validating the time of every raw observation prevent hindsight leakage when an AI agent joins records through a versioned alias map or computes a derived feature? **No.** The mapping and every other dependency must also have been knowable at decision time.

## Prototype

`lineage.py` implements (1) a bitemporal mapping selector requiring both `effective_at <= decision` and `captured_at <= decision`, (2) a transitive dependency-DAG gate that computes the maximum of both times for every ancestor, (3) fallback to an older complete revision when a newer revision has late dependencies, and (4) fail-closed checks for missing nodes, cycles, and invalid negative timestamps.

## Evidence

Run `python test_lineage.py` and `python benchmark.py` in this directory. All **14/14 tests passed**, including **2,000 randomized DAG closure checks**. The deterministic benchmark uses **2,000 synthetic cases per domain**:

| Domain and failure mechanism | Naive accuracy | Guarded historical fallback accuracy | Guard result |
| --- | ---: | ---: | --- |
| SEO: backdated keyword/entity alias map first captured after decision | 100.0% (2,000/2,000) | 49.3% (986/2,000) | Excluded all 2,000 future mapping revisions |
| Gold: derived conversion depends on future-captured coefficient, although price and derived record claim old timestamps | 100.0% (2,000/2,000) | 50.8% (1,016/2,000) | Rejected all 2,000 future-dependent features; accepted 2,000 old fallbacks |

**Important:** These 100% naive results are *constructed adversarial examples*: the late mapping/coefficient was deliberately set equal to the future label. They do not measure the performance of real gold or SEO prediction systems. Accuracy of the guarded historical fallback is approximately chance because the fallback was sampled independently of the labels. The value is the reproducible leakage counterexample and prevention in the stated model, not predictive accuracy.

## Counterexamples and limitations

- An early-captured raw row with `effective_at > decision` is invalid despite early capture; tested.
- An early-captured mapping may depend on a late-captured third-party table; a top-level timestamp-only check fails, but DAG closure rejects it; tested.
- A newer invalid mapping must not block fallback to an older complete mapping; tested.
- **Forged capture timestamps** or **omitted dependency edges** cannot be detected by this model. The graph and timestamps require independent evidence; a test confirms forged timestamps pass.
- A mapping that was publicly available earlier but only captured later is conservatively excluded; this may reduce historical coverage. Nothing here authenticates timestamps, proves historical agent access, or establishes production safety.

## Transferable lesson

Point-in-time validation is a **dependency-closure property**, not a row-level timestamp filter. Preserve the complete provenance graph and separate business effective time from independently witnessed capture time. In real pipelines, use source snapshots or immutable as-of joins, not the latest lookup tables.
