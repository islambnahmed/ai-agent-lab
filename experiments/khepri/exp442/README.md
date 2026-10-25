# Khepri exp442 — cancellation barriers and in-flight delivery

2026-10-25. Self-contained Python standard-library simulation; no external actions.

## Question and prior evidence

Exp441 checks that a delivery claim is valid **before** invoking a separate sink. Does a later cancellation prevent an already-validated dispatch from applying its effect? The exp441 README explicitly lists cancellation/revocation as open work. This experiment models the timing boundary rather than claiming a defect in GitHub, Notion, or Drive.

## Competing hypotheses

- **H0 — outbox-only cancellation is sufficient:** a cancelled job cannot produce an effect.
- **H1 — cancellation must be serialized with the effect at the destination:** cancellation may only report success after the destination durably rejects future effects for that operation ID.

The baseline model validates the claim before dispatch, as exp441 does, but then permits cancellation and the effect to race. Enumerating its three ordered interleavings yields **two unsafe schedules**: `verify → effect → cancel` (false cancellation success after a completed effect) and `verify → cancel → effect` (in-flight effect after cancellation). If cancellation precedes verification, verification fails.

## Prototype

`cancellation.py` models a cooperating destination using SQLite WAL and `BEGIN IMMEDIATE` for atomic, mutually exclusive effect and cancellation decisions. `cancel_guarded` inserts a durable fence only if no effect exists, returning `cancelled` or `too_late`. `apply_guarded` atomically checks the fence, returning `fenced`, `applied`, or `duplicate`. A successful cancellation is a **destination-side barrier**, not merely an outbox status flag. The outbox should only report success after that barrier is durably confirmed; if a response is lost, retry cancellation using the same stable ID. This prototype deliberately does not implement outbox status reconciliation.

The abstract guarded model enumerates all six ordered interleavings of dispatch verification/effect and cancellation fence/finalization. **Zero violate** the invariant `cancel_success => no effect`. This property holds under the model's atomic destination transactions, not under arbitrary real-world network semantics.

## Reproduction

From this folder, Python 3.10+ (standard library only):

```bash
python -m unittest -v test_cancellation
python benchmark.py
```

`benchmark_results.json` is the recorded output. Ten tests passed. The randomized test covers 1,000 operation IDs across two materially different example domains (`seo`, `gold`), shuffled apply/cancel/retry operations, and simulated process restarts. The SQLite test also checks two connections, duplicate dispatches, and payload conflicts.

## Deliberate counterexample to the fix

Deleting a successful cancellation's fence (a tombstone) and later replaying the same ID **does permit an effect**. The test intentionally deletes the fence to demonstrate the failure. Retain cancellation tombstones for at least the entire possible replay window; when the replay horizon cannot be bounded, deletion cannot be assumed safe. This is not a safe tombstone-GC implementation.

## Limits / next engineering step

- Requires the actual effect destination to participate in the same atomic cancel-vs-effect decision. An independent outbox cannot force this on a remote service.
- Does not solve an effect already committed before cancellation; returns `too_late`, not a false success. Reversal, if possible, is a separate compensating operation.
- Does not cover malicious sink writes, external side effects outside the transaction, DB loss, split-brain destinations, or multi-operation workflows.
- If the sink is unreachable or lacks fencing, report `unknown`/`cancellation_requested` rather than claiming cancellation success. Never blindly retry an irreversible effect.
- This is a model of a contract, not production authorization, cancellation of GitHub/Notion/Drive operations, or a proof of distributed exactly-once execution.

**Reusable lesson:** cancellation has a linearization point at the effect destination. Reliable agents must distinguish `requested`, `confirmed_cancelled`, and `too_late`; an outbox-only cancellation flag is not a reliable completion receipt.
