# Khepri exp401 — Crash-window delivery and cross-runtime hash counterexample

**Scope:** authorized AI Agent Lab only. No external API calls or side effects. The destination is a separate local SQLite database, not a real gold/SEO service.

## Question
Exp391 correctly distinguished authorized intents and reserved them atomically, but explicitly left a `reserved` record after a crash **ambiguous**. Can a local ledger alone ensure one downstream effect across crash boundaries? Does its JS payload canonicalization agree with a naive Python port?

## Experiment
Copied `sqlite_ledger.py` unchanged from the exp391 local artifact (SHA-256 `4374ea116bce638e5e84a855190cf7fa07e13580cfbf5442e9220f7770c1c297`). Used separate SQLite databases for ledger and destination to model non-atomic cross-system delivery. Simulated crashes after reservation, after destination commit, and after local completion; retried using three strategies:

1. `replay`: blindly repeat a reserved intent to a non-idempotent destination.
2. `freeze`: never retry an ambiguous reserved intent.
3. `keyed`: repeat using the same intent key at a destination enforcing **atomic** unique-key insertion and payload conflict detection.

Tested both `gold.receipt.issue` and `seo.page.publish`. For each, the benchmark exhausts 16 pairs of crash/no-crash cuts (plus a final successful attempt); tests additionally exhaust 64 three-cut sequences per domain for `keyed`.

## Verified local results

| Strategy | Gold: 0 / 1 / >1 effects (16) | SEO: 0 / 1 / >1 effects (16) |
|---|---|---|
| replay | 0 / 11 / 5 | 0 / 11 / 5 |
| freeze | 4 / 12 / 0 | 4 / 12 / 0 |
| keyed | 0 / 16 / 0 | 0 / 16 / 0 |

**10/10 unit tests passed**, including 128 three-cut `keyed` scenarios (64 per domain). A check-then-act interleaving produced two effects because a status query is not an atomic reservation. A payload change under the same intent was rejected before a second effect.

**Second counterexample:** The exp391 JS canonicalizer hashes `{v:1}` and `{v:1.0}` identically; Python `json.dumps` produces `1` and `1.0` respectively. Thus a naive Python port yields a different payload hash for numerically equal values, even though the ASCII-only intent key matched in a direct JS/Python test. Cross-language hash equivalence is **not established** for arbitrary JSON. Adopt a vetted common canonicalization specification (e.g. RFC 8785/JCS) or pass canonical bytes from one trusted producer before deploying across languages.

## Reproduce

Python 3.10+; Node 22+ for the cross-runtime fixture test; standard library only:

```bash
python3 -m unittest -v test_crash_recovery.py
python3 benchmark.py
```

## Interpretation and limits
The experiment is a **simulation**, not evidence that an external provider offers atomic idempotency. The `keyed` guarantee holds only while the destination enforces the unique key transactionally, keeps its deduplication record, and uses a stable trusted intent ID. It does not cover retention expiry, lost ledger files, key collision attacks, network partitions across different destination replicas, real vendor contracts, or inconsistent canonicalization. A local reservation cannot alone prove remote execution. No claim of exactly-once execution against real services, no modification to `main`.

## Next test
Before any integration, probe an actual **authorized test double** or documented vendor API contract for destination-side atomic idempotency, key retention, and conflict behavior; avoid external writes without explicit authorization.
