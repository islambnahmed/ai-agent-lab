# Khepri exp440 — crash-recovery delivery, receipt retention, and the exactly-once boundary

**2026-10-25 | offline SQLite fault injection | no external side effects**

## Question and prior work

Exp438 demonstrated that a single-use authorization permit can be consumed before an external action takes effect, losing the action on crash. Exp439 established that an authorization check must bind to the prepared wire action, but explicitly did not solve durable delivery. This experiment asks: **what guarantees can a durable outbox, leased workers, and an idempotent sink actually provide across process crashes?** And when do those guarantees fail?

## Prototype

- A durable **outbox** records an immutable operation ID, exact payload bytes, and digest. Re-enqueueing the same ID with different bytes is rejected. Workers claim pending work with an expiring lease and incrementing generation. An ACK is fenced to the claiming generation.
- An **idempotent destination** records an operation receipt and its simulated effect **in the same transaction**. If a worker retries after the effect but before ACK, the receipt suppresses a second effect. Conflicting payloads under an existing operation ID are rejected.
- Explicit fault injection crashes workers after claim or after effect but before ACK. Reopening the database simulates process restart. No remote API is called.

This is a **contract simulator**, not an integration. The sink is modeled in the same SQLite database as the outbox for convenience, but there is **no transaction spanning outbox claim, sink effect, and ACK**. In production, the *remote sink itself* must enforce atomic receipt/effect semantics, or the agent must reconcile outcomes; a local SQLite receipt cannot prove a remote write succeeded. The module assumes trusted, already-authorized prepared action bytes; it does not implement exp439's authorization gate or validate actual GitHub/Notion/Drive descendants.

## Reproduce

Run from this directory:

    python -m unittest -v test_durable_delivery.py
    python benchmark.py

## Evidence

- **15/15 local unit tests passed**: normal delivery; immutable ID/payload binding; process restart after claim, effect, and ACK; two-connection lease exclusion; stale ACK fencing; late worker retries; digest conflicts and tampering; sink rollback on injected write failure; TTL receipt-loss counterexample; and transfer to two different task families.
- **Deterministic fault matrix:** 200 SEO and 200 gold operations, each interrupted after a sink effect but before ACK (400 injected crashes). After reopening and retrying, **400 effects** total, **400 suppressed duplicate deliveries**, **0 duplicate effects** in this synthetic sink with durable receipts.
- **Competing hypothesis falsified:** repeat the fault matrix with the receipt ledger purged before retry. For 200 SEO and 200 gold *new* operations, **400 extra effects** occur (200 duplicate effects per family). A lease and stable ID alone do **not** prevent duplicates once the sink forgets prior IDs.
- **Transactional counterexample:** a SQLite trigger forces effect insertion to fail; the receipt insert rolls back in the same transaction. The action succeeds after the trigger is removed. Recording a receipt separately from the effect could incorrectly suppress a never-applied operation.

## Limits and decisions

- This demonstrates **at-least-once attempts with duplicate-effect suppression under specific assumptions**, not a universal exactly-once guarantee. Durable sink receipts must outlive *all possible retries* (or use monotonic sequence watermarks with proven no-reuse/ordering invariants). TTL without such a bound is unsafe.
- An old worker can still reach the sink after losing its lease; generation fencing prevents stale **ACKs**, not stale **remote effects**. Stable idempotency IDs suppress duplicates if the destination honors them. Cancellation or changing authorization policy after enqueue requires a separate policy check at dispatch.
- Crash injection is deterministic, not a real distributed network failure; no malicious worker, clock drift, multi-region partition, corrupt disk, or actual service rate limits were tested.
- If the sink does not offer idempotent operations, use read-after-write reconciliation and an explicit **uncertain outcome** state. Do not automatically retry irreversible, non-idempotent effects.

## Transferable lesson

**Authorization binding and reliable delivery are independent contracts.** Bind the permitted action to exact wire bytes (exp439), enqueue it durably, retry with a stable operation ID, make the destination atomically deduplicate the ID and effect, and fence stale worker ACKs. A finite receipt-retention policy invalidates the duplicate-suppression claim unless the retry horizon is strictly bounded or a stronger no-reuse protocol is enforced.
