# Lumen 371 — Historical replay commitment guard (synthetic lab study)

**Date:** 2026-10-23. **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`. **Type:** local, reversible code experiment. No external timestamp service, signer, or independent attestor was contacted.

## Research question

Lumen 370 isolates a historical evaluation from *future* malformed records, but the selected history is still self-declared. If an adversary rewrites the timestamp or inserts a plausible **backdated** correction before the cutoff, historical replay can silently compute a different historical state. Can we detect that change without preventing legitimate later sibling versions and corrections?

## Mechanism

`lumen371.py` provides `make_replay_commitment(...)` and `verify_replay_commitment(..., expected_digest)`. Both reuse `lumen370.historical_snapshot` for scoped validation. A deterministic SHA-256 digest commits to canonical JSON containing:

- schema identifier and ordered case frame;
- the full frozen base ledger (including original source declarations and receipt order);
- only the selected version lineage and its correction prefix visible at the cutoff;
- selected version ID, UTC cutoff, threshold, and final-only policy.

Verification compares the recomputed digest with a **separately supplied, previously trusted digest** using `hmac.compare_digest`. It fails closed on mismatches or malformed digests. Future unrelated versions and future corrections on the selected path do not alter the committed historical payload. Changes to historical labels, metadata, receipt timestamps, or evaluation policy do alter it.

**Critical trust boundary:** A hash computed from the current potentially compromised ledger is *not* independent evidence. An attacker who can rewrite both the ledger and its stored digest can forge a consistent pair. This study provides only a tamper-evidence primitive conditional on **prior independent custody of the reference digest**. The API deliberately returns `independent_digest_custody_verified=False`; it does not authenticate time, source, or truth of labels.

## Reproducible fixture

Four cases with final labels `[1,1,0,0]`, root `v1`, and `v2` correcting `C1:1→0` at 12:15 UTC. At cutoff 12:16 UTC, the error rate is 25%, so the evaluator accepts under a 40% threshold. A new valid-looking correction `C2:1→0` inserted at 12:12 UTC, **before** the existing correction in the list, is accepted by the scoped replay's chronology rules and changes the computed rate to 0%. However, the independently retained original digest no longer matches, so the guarded replay raises `LedgerError`. Adding an invalid *future* sibling at 13:00 or future correction at 12:40 leaves the original digest valid, preserving Lumen 370's historical isolation.

A deliberately adversarial test recomputes the digest *after* inserting the backdated correction: that new digest passes comparison against the tampered ledger, proving why independent custody of the original digest is necessary.

## Tests and limitations

Local commands from `research/lumen`:

```sh
python -m unittest -q test_lumen370.py test_lumen371.py
python -O -m unittest -q test_lumen370.py test_lumen371.py
```

Both commands passed **25 unittest methods** each (12 inherited Lumen 370 tests + 13 Lumen 371 tests). The new tests include 200 seeded metadata/timestamp mutations. These are synthetic tests, not an operational security audit. The local copies of `lumen366.py` and `lumen368.py` were reconstructed from inspected GitHub connector source, but are **not byte-identical** to the repository versions; the `lumen370.py` and `test_lumen370.py` files used locally do match the previously published Git blob SHAs. CI and testing against the exact dependency blobs on GitHub remain unverified.

## Next useful step

Cross-run the tests against the exact repository dependencies in CI or a clean checkout. Then design an authorized independent custody model for historical digest anchors, such as a separately permissioned append-only lab record, without claiming that a same-writer hash or a Git commit by itself proves real-world event time. Do not contact outside services or change security settings.

## Recovery

Files: `research/lumen/lumen371.py`, `test_lumen371.py`, this report. Dependencies: `lumen366.py`, `lumen368.py`, `lumen370.py`. Treat this as a separate optional guard, not a silent replacement of the strict or scoped replay APIs.
