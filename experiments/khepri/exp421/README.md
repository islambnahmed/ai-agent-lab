# Khepri experiment 421 — SQLite atomic approvals under concurrency, crashes, and delete/recreate

**Date:** 2026-10-24. **Authorized scope:** `islambnahmed/ai-agent-lab`. **Status:** local, reproducible, defensive research prototype; no external resource writes.

## Question and hypothesis

Exp420's in-memory `FakeStore` prevented stale writes under a single-process lock. Does that lesson survive **multiple OS processes**, **transaction failure**, and **delete/recreate** of the same path? Can an accidental SQL writer bypass a version check?

**Hypothesis:** an SQLite transaction (`BEGIN IMMEDIATE`) combining receipt redemption, monotonic per-path revision checking, and the content update should preserve the one-use and no-stale-overwrite properties across processes. A tombstone ledger should close the delete/recreate revision-reset hole. Schema triggers should close accidental direct-SQL writes that forget to bump the revision.

## Reusable prototype

`approval_sqlite.py` implements a **synthetic** approval database using only Python's standard library and SQLite. `heads` persists revisions even for deleted paths (`present=0`); `approvals` stores one-use, path- and payload-bound test records. `redeem` checks and changes state in a single SQLite write transaction. Schema triggers increment revisions for content/presence updates that omit a revision bump, reject physical deletion of `heads` rows, and reject revision regression. A rejected stale attempt consumes a valid receipt; a malformed plan/payload does not.

The approval ID is only a local test identifier, **not** a credential or authorization proof. `issue` presumes an action has already been independently authorized. `external_write` is a test helper, not an authorized external tool.

## Reproduce

```bash
cd experiments/khepri/exp421
python -m unittest -q test_approval_sqlite.py
python benchmark.py
```

**Local observation:** 20/20 unit tests passed, including:

- two **separate OS processes** redeeming different approvals based on the same resource version: exactly one succeeds and the other receives `stale`;
- three separate processes attempting to redeem the same approval: exactly one succeeds;
- a subprocess terminating with `os._exit(77)` before committing a staged write: SQLite rolls back both receipt consumption and the content change; the approval can then be redeemed;
- seeded independent reference-model checking across **1,200 mixed operations** on SEO and gold-labeled paths;
- delete/recreate, ABA, missing-path creation races, path/payload mismatch, and unrelated-path updates;
- direct SQL content update without revision bump: accepted by the unprotected variant, detected by the trigger-protected variant;
- naive check-then-write and naive per-row revision reset counterexamples.

The paired deterministic benchmark exercises **480 synthetic cases** (240 each for `seo` and `gold`; 40 of each of six event types per domain):

| Metric | Naive unconditional write | SQLite version-bound redemption |
| --- | ---: | ---: |
| Overwrites of a newer state after an intervening same-path event | **320** | **0** |
| Clean/unrelated updates accepted | 160 | 160 |
| Stale approvals rejected | 0 | 320 |

Scenarios: clean, intervening write, ABA (change then restore), delete/recreate, unrelated-path write, and absent-path create race. Counts are deliberately constructed, **not** estimates of production failure rates. See `results.json` for per-domain breakdown.

## Falsifying counterexamples and corrections

1. **In-memory locking does not establish cross-process safety.** The previous experiment was not tested against independent OS processes; this experiment adds actual SQLite multi-process contention and crash rollback.
2. **A revision stored only on the resource row can reset after delete/recreate.** A prior approval at revision 1 may falsely appear current when a deleted row is reinserted at revision 1. Persistent tombstones avoid this in the prototype.
3. **Direct SQL writes without version updates defeat an API-only guard.** The test first reproduces the failure with triggers disabled, then confirms a trigger bumps the revision and causes stale redemption to be rejected.
4. **Checking state and writing in separate transactions is unsafe.** A barrier-synchronized two-thread counterexample shows both naive workers observing revision 1 and both writing based on it.

## Limitations and next decisions

- SQLite's guarantees depend on local filesystem, SQLite locking, transactions, and configuration; this is **not** a distributed database or a GitHub/Notion/Drive atomic writer. Real remote APIs need their own conditional-write mechanism (e.g., an actual supported compare-and-swap contract).
- A principal able to alter or drop database triggers, replace the database, manipulate the process, or issue arbitrary SQL with full schema privileges is **outside this model**. The triggers guard accidental SQL paths, not malicious DB administrators. Path normalization, trusted issuance, issuer compromise, and real identity/authentication are not addressed.
- Receipt IDs are predictable synthetic labels; do **not** deploy this as an approval service. Hashing binds bytes but does not authenticate the issuer. No secrets are used.
- The crash test models rollback before commit; it does not validate disk durability under actual power loss, networked storage, or multi-host coordination.
- `BEGIN IMMEDIATE` serializes writers for the whole SQLite database; it prioritizes correctness over concurrency and may become a throughput bottleneck. No performance or availability SLA is claimed.
- A stale receipt must be reconsidered against new state and newly authorized, not automatically reissued. A malicious worker with write access can cause denial of service by repeatedly changing state.

**Transferable lesson:** approvals for mutable resources require a transactional execution boundary, a revision history that survives delete/recreate, and coverage of **every** write path. A successful in-memory simulation is useful evidence but not sufficient proof of cross-process correctness.
