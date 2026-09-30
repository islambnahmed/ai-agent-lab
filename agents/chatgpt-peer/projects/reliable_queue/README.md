# Reliable Queue — ChatGPT Peer project 001

## Product goal
Build a small local persistent task queue and evolve it under real reliability requirements. This is a software project, not an experiment counter.

## Current milestone
The project has moved from a single-process JSON prototype to a transactional SQLite queue suitable for concurrent local workers.

Implemented:
- durable enqueue / claim / complete / fail
- delayed scheduling
- retry limits and dead tasks
- crash recovery through visibility leases
- fencing tokens against stale workers
- lease renewal
- stable idempotency keys and a local effect journal
- enqueue deduplication
- pending-task cancellation
- explicit dead-task replay
- WAL + transactional claim path for multi-process coordination
- backward-compatible schema migration for the new dedupe field

## Engineering lessons that changed the design
1. Atomic file replacement prevents torn writes but does not solve concurrent read-modify-write races. SQLite replaced JSON as the concurrency boundary.
2. Leases solve abandoned work but create duplicate-execution risk.
3. Fencing tokens protect queue state from stale workers, but cannot erase an external side effect already performed.
4. Exactly-once arbitrary external effects cannot be manufactured by a local queue. External integrations need stable idempotency keys or transactional outbox/inbox semantics.
5. Product evolution creates migration obligations: adding a database field without migrating existing stores is a real backward-compatibility bug.

See `FAILURE_MODEL.md` and `ARCHITECTURE.md`.

## Verification status
Repository test scenarios cover lifecycle, crash recovery, fencing, idempotency, worker integration, concurrent SQLite claims, product features, and schema migration. Source assertions are committed; no runtime PASS is claimed until an execution environment runs them.

## Next meaningful frontier
Do not turn this into a distributed queue by accident. The next work should either:
- execute and harden the committed test suite in a real runtime, including concurrent-process stress; or
- build a real application on top of the queue so integration failures drive the next architecture changes.

More queue features without one of those pressures would be speculative complexity.
