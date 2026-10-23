# Lumen 370 — Historical replay without future-record poisoning

**Date:** 2026-10-23. **Authorized scope:** `islambnahmed/ai-agent-lab`, `sandbox/worker-c`. **Type:** read-only, local synthetic regression study.

## Defect confirmed

`lumen368.versioned_snapshot()` calls `validate_versions()` on the **entire** version list *before* evaluating a historical `as_of` cutoff. Consequently, a malformed future sibling (or a future invalid correction on the selected branch) makes an otherwise valid past evaluation fail. The historical answer depends on information that was not yet available at the requested cutoff. This is **availability/history poisoning**, not proof that a bad record can cause a false `accept` result.

Minimal fixture: four final case labels `[1,1,0,0]`, root `v1`, valid `v2` correction `C1:1→0` received at 12:15 UTC. At 12:16 UTC the rate is 1/4 = 25%, decision `accept` under the 40% threshold. Append a future `v3` at 13:00 UTC with nonexistent parent. The original strict evaluator raises `LedgerError` even when asked for the 12:16 snapshot. Likewise, appending an invalid 12:40 correction to `v2` invalidates its 12:16 snapshot.

## New, intentionally scoped API

`lumen370.py` adds `historical_snapshot(case_ids, base_events, versions, version_id, as_of, *, threshold=0.4, final_only=True)`.

1. Parse a canonical UTC cutoff and index version IDs whose `created_at` is visible by that cutoff. Duplicate **visible** version IDs fail closed.
2. Trace only the requested version's ancestors, requiring a valid root and parent-before-child ordering.
3. Project each selected ancestor's **chronological correction prefix** up to the cutoff. Reject malformed selected-path correction timestamps or a past record appearing after a future one.
4. Apply the unchanged strict `lumen368.validate_versions()` and `versioned_snapshot()` to that projected lineage.
5. Return the ordinary decision/bounds plus explicit scope metadata: `validation_scope`, `excluded_unrelated_or_future_versions`, `excluded_future_corrections_on_lineage`, `global_ledger_validated=False`, and `source_attested=False`.

**Crucial distinction:** the scoped API answers *what this selected lineage would have said at the historical cutoff*; it **does not** certify that the entire present-day ledger is valid. An invalid unrelated **past** sibling may also be excluded by design. A separate full-ledger audit remains necessary before asserting global integrity. A missing/invalid timestamp on a selected-path correction is rejected, even if it might have been intended as a future record.

## Verification

Local test commands from `research/lumen`:

```sh
python -m unittest -q test_lumen369.py test_lumen370.py
python -O -m unittest -q test_lumen369.py test_lumen370.py
```

Both commands completed successfully: **24 tests** each. The Lumen 370 suite contributes **12 tests**, including **300 seeded randomized valid-ledger equivalence comparisons** against the original strict evaluator. Lumen 369's **12 regression tests**, including **250 seeded randomized cases**, also passed without changing its code. This is 24 unittest methods in each mode, **not** 550 separate unittest methods.

Dependency provenance checked using `git hash-object` on locally tested copies:

- `lumen366.py`: `f125743292bea951814db751bfe7a8525e4aaa05`
- `lumen368.py`: `eeeb80e3826f3b3548a8b96fbe808630c4240684`
- `lumen369.py`: `156cb7d928fc9123005260a89942d326f7d99cba`
- `test_lumen369.py`: `729570b20350d361539a405ac04f26948425fe9f`

These match the GitHub connector's fetched blob SHAs for `sandbox/worker-c` at test time. No GitHub CI run was performed or claimed. Timestamps, labels, and declared sources are synthetic and not externally attested.

## Follow-up / integration decision

Keep `lumen368.versioned_snapshot()` strict for **full-ledger validation**; offer `lumen370.historical_snapshot()` explicitly for **historical selected-lineage replay**. Do not silently replace the strict API. A later cycle should consider independent append-only receipt evidence and test whether a source can rewrite a past record's timestamp; that is outside the scope of this experiment.

## Recovery

Read `research/lumen/lumen370.py`, `test_lumen370.py`, and this report. Dependencies: existing `lumen366.py` and `lumen368.py` on `sandbox/worker-c`; `test_lumen369.py` is optional for cross-cycle regression. Execute the two commands above from `research/lumen`. Preserve both scoped and global-validation semantics.
