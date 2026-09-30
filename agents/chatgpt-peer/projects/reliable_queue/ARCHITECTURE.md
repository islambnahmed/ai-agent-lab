# Architecture evolution

## Why JSON stopped being enough
Atomic file replacement protects a single write from partial-file corruption, but it does not provide safe read-modify-write coordination across multiple processes. Two workers can load the same old snapshot and later overwrite each other's changes.

Adding an ad-hoc lock would make the JSON file a miniature database. The project therefore adds a SQLite backend instead.

## SQLite backend
`sqlite_queue.py` uses:
- WAL mode;
- `BEGIN IMMEDIATE` around claim/recovery;
- conditional updates;
- leases and fencing tokens;
- durable retry/dead state.

This moves concurrency control into a transactional store rather than pretending atomic rename solves concurrent state mutation.

## Delivery semantics
The queue is intentionally **at least once**. Exactly-once delivery is not promised. Stable idempotency keys are the integration contract for side effects.

## Current architectural boundary
SQLite makes a strong local/multi-process queue. It is not a distributed consensus system and should not be stretched into one. A future distributed version should use a storage/service designed for distributed coordination rather than layering network assumptions onto this backend.
