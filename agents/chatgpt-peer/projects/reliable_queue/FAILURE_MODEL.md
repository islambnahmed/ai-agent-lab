# Failure model

The project now distinguishes three guarantees.

1. **Queue durability**: atomic local state replacement reduces partial-write corruption.
2. **At-least-once delivery**: expired leases allow abandoned work to be retried.
3. **Fenced queue mutation**: stale workers cannot complete/fail a newer claim.

Exactly-once arbitrary external side effects are **not** claimed.

A local idempotency journal suppresses repeated effects only when the effect itself is safely represented by the journal, or when an external service honors the supplied stable idempotency key. There is an unavoidable crash window if an arbitrary external effect succeeds and the process dies before the local journal records success.

Therefore the worker passes a stable key (`task:<id>`) to handlers. Integrations should forward that key to idempotency-aware external systems, or use a transactional outbox/inbox design when the resource supports transactions.

This limitation is a design result, not an implementation TODO that can be fixed by another local flag.
