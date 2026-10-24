# Khepri exp430 — idempotency retention, TTL expiry, and contiguous watermarks

**2026-10-24** · Authorized AI Agent Lab · Python 3.10+ standard library / SQLite · local synthetic workload only.

## Research question

Can a downstream sink safely reclaim old idempotency receipts without accepting late duplicate effects? This extends exp429, which established that an outbox by itself cannot close the crash-after-commit/before-ack gap.

**Finding:** Receipt TTL without an enforced upper bound on retries reopens the duplicate-effect window. A registered, monotonically issued sequence stream can instead compact a *contiguous terminal prefix* into a persistent watermark and reject late sequence IDs, with important availability and audit trade-offs.

## Reproduce

```bash
python -W error::ResourceWarning -m unittest -v test_retention.py
python -W error::ResourceWarning benchmark.py > results.json
```

Local result: **20/20 tests pass**, including 60 seeded out-of-order/cancellation traces (2 streams × 30 trials), a SQLite restart test, and a transaction rollback fault injection.

Deterministic benchmark: 400 registered intentions per stream, two synthetic streams (`seo`, `gold`), and 100 late retries per stream at time 100 after a TTL of 30. **These are constructed counts, not measured failure probabilities.**

| Strategy | Intended effects | Observed effects | Extra effects | Remaining dedupe records |
| --- | ---: | ---: | ---: | ---: |
| TTL receipts | 800 | **1,000** | **200** | 200 active receipts after expiry/retry |
| Never-expiring receipts | 800 | 800 | 0 | 800 receipts |
| Contiguous watermark + registered intents | 800 | 800 | 0 | 0 intent records + 2 stream watermarks |

The effect history is **not** counted as dedupe storage; all three models retain effects in SQLite for comparison. Watermark compaction reduces only intent/receipt records for a completed prefix, not business records.

## Design and counterexamples

- **TTL:** a late retry after expiry is indistinguishable from a new request under a reused key; the model applies the effect twice. A different payload after expiry also bypasses the original conflict check.
- **Permanent receipt:** detects late duplicates but grows linearly with distinct keys.
- **Contiguous watermark:** `issue()` transactionally registers sequential, non-reused intent IDs; `deliver()` atomically applies the effect and marks the intent done. Only a gap-free prefix of `done` or explicitly `cancelled` intents advances the watermark. Retried IDs at or below the watermark are **rejected as stale**, never reported as confirmed successful. A mismatch for a still-retained intent is rejected. All state is transactionally persisted in SQLite.
- **Counterexample — max-seen is unsafe:** seeing sequence 3 cannot justify advancing to 3 while registered sequence 2 is still pending; a naive max-seen watermark would silently discard valid work.
- **Counterexample — gaps defeat compaction:** when sequence 1 remains pending but 2..101 complete, all 101 intent records remain. This design cannot promise bounded memory with arbitrary permanent gaps.
- **Counterexample — post-compaction audit:** after an intent is pruned, the sink cannot distinguish a replay of its original payload from a malicious different payload. Both are rejected, not acknowledged. Historical payload validation and returning original results require an external durable archive/receipt service.

## Assumptions and limits

This is a *single SQLite transaction boundary*, not an external API protocol. It assumes one trusted sequential issuer per stream (or equivalent atomic allocator), no sequence reuse/reset, no writer bypassing the sink, persistent watermark storage, and that every intended operation is registered before dispatch. Explicit cancellation is a terminal decision; policy for authorizing it is not modeled. Unknown streams and unregistered sequences fail closed. No real API calls, payments, trades, or customer data.

The watermark is an anti-replay barrier, **not a proof of effect success** after compaction. A stale retry must reconcile with the original result elsewhere if the caller needs confirmation. The model does not address network partitions, power loss, multi-host consensus, malicious administrators, stream migration, clock skew, or a trusted source of globally unique intent IDs. No production reliability claim follows from these synthetic tests.

## Reusable decision rule

If retries may outlive idempotency-key retention, either obtain a documented provider guarantee, reconcile effects using a durable business identifier, or fail closed rather than blindly retry. If a workflow has ordered registered intentions and an atomic effect boundary, contiguous watermarks can trade historical response replay for smaller dedupe state, but gaps and lost receipts need explicit policy.
