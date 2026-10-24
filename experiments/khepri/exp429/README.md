# Khepri exp429 — durable outbox vs exactly-once illusion

**Date:** 2026-10-24. **Scope:** authorized AI Agent Lab, local synthetic experiment. Python 3.10+ standard library, two separate SQLite files, no external APIs or real customer data.

## Question

When an AI agent executes a downstream operation, can a durable local outbox alone prevent duplicate side effects if the worker crashes **after the downstream commit but before the local acknowledgement**?

**Answer from this model: no.** An outbox makes retries durable but cannot know whether a remote operation committed. A stable, scoped idempotency key and **atomic deduplication at the downstream effect boundary** are additionally needed for the tested exactly-once *effect* property. This is not a general exactly-once delivery guarantee.

## Design

`outbox.py` provides:

- `Outbox`: SQLite-persisted pending/done jobs; crash/restart preserves pending jobs; immutable job identity rejects conflicting payloads; scoped IDs use canonical JSON tuples to avoid delimiter collisions.
- `IdempotentSink`: a **separate SQLite database** that writes effect and deduplication receipt in the **same transaction**. A retry with identical key/payload returns `replayed`; conflicting payload returns an error.
- `NonIdempotentSink`: negative control without sink deduplication.
- `SplitCommitSink`: negative control that commits an effect before a receipt; a crash between them duplicates the effect on retry.

Fault injection covers worker crashes before sink call, after sink commit but before outbox ack, and after ack. A real subprocess exits with `os._exit(23)` after the sink commit; the parent restarts the job. A second test injects a failure **inside** the sink transaction, confirming rollback of both effect and receipt. Two separate OS processes race to apply the same key to the sink.

Synthetic transfer cases: `seo` lead events and `gold` quote ingestion. The labels are just data; no actual lead delivery, trading, prices, or third-party writes occur.

## Reproduce

From this directory:

```bash
python -W error::ResourceWarning -m unittest -v test_outbox.py
python benchmark.py > results.json
```

**Observed locally:** 16/16 tests pass. Deterministic benchmark: 2 domains × 5 scenarios × 200 unique jobs = **2,000 unique jobs per sink variant**. The two variants use identical synthetic workloads.

| Scenario (400 jobs across both domains) | Effects without sink dedupe | Effects with atomic sink dedupe | Intended effects |
| --- | ---: | ---: | ---: |
| clean | 400 | 400 | 400 |
| crash before sink | 400 | 400 | 400 |
| crash after sink, retry | **800** | **400** | 400 |
| two crashes after sink, retry | **1,200** | **400** | 400 |
| crash after ack, retry | 400 | 400 | 400 |
| **Total** | **3,200** | **2,000** | **2,000** |

The naive sink produced **1,200 extra effects** in deliberately fault-injected cases; the atomic sink produced **zero extra effects** under these assumptions. These are designed counts, not incident rates or real-world reliability estimates. See `results.json`.

## Falsifying counterexamples

1. **Outbox alone fails:** after the sink commits but before local ack, retry sends the same job again. A non-idempotent sink duplicates effects.
2. **Ack-before-send loses work:** if local state becomes `done` before the sink is called and the worker dies, the effect is never executed.
3. **Non-atomic dedupe fails:** if the sink commits the effect and only later records its receipt, a crash between the commits causes duplication even though a receipt table exists.
4. **Key reuse can silently merge two real intentions:** when two distinct intended operations mistakenly share *both* key and payload, the sink cannot distinguish them. Scoped key allocation and unique intent identity are external responsibilities.
5. **Shared key, different payload is rejected:** this prevents silent overwrites but may require operator intervention and can block progress.

## Assumptions and limits

- The sink transaction must atomically cover the **actual side effect** and the receipt. Sending email, posting to a remote API, or calling a payment service **cannot** be made atomic merely by wrapping a local SQLite receipt. For those sinks, use a provider-supported idempotency contract or design compensations/reconciliation.
- Local SQLite atomicity is not a distributed guarantee, and this experiment does not test power-loss durability, replication, network partitions, database corruption, idempotency-key expiry, multi-tenant authorization, or malicious administrators.
- The outbox has no worker lease, backoff, dead-letter queue, observability, or fairness policy. Duplicate dispatch is tolerated by the modeled sink; availability and throughput are not benchmarked.
- Exactly-once **effect** is conditional on stable keys, sink enforcement, retention of receipts, and one transaction covering the effect and dedupe record. It is **not** exactly-once message delivery or universal exactly-once semantics.
- The synthetic sink assumes all write paths respect the receipt transaction; bypass writers and downstream services outside the transaction are out of scope.

## Transferable lesson

A durable outbox solves **retry persistence**, not the **uncertain-acknowledgement window**. Choose the idempotency boundary at the actual side effect, test crashes on both sides of that boundary, and include a negative control that deliberately breaks receipt atomicity. For real agent workflows, first classify each downstream API as provider-idempotent, reconcilable, compensatable, or unsafe-to-retry.
