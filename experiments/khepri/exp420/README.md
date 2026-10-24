# Khepri experiment 420 — Version-bound approvals at the tool boundary

**Date:** 2026-10-24. **Scope:** `islambnahmed/ai-agent-lab` only. **Status:** tested simulated prototype; no external writes or production systems touched.

## Question and independent hypothesis

Exp419 binds a one-use approval to a plan and payload. Does that prove an approved write is still appropriate **when the destination changes between approval and redemption**?

**No.** Even with a correct immutable plan and byte digest, a different worker can change the destination in the meantime. A subsequent approved write may overwrite the newer result. This is a resource-state time-of-check/time-of-use (TOCTOU) problem, independent of receipt or plan tampering.

## Prototype

`state_bound.py` models an authorized-path approval and a fake in-memory store. It compares:

- **Baseline:** approval binds plan and payload but permits writing at any later resource version.
- **Version-bound:** approval also captures the resource's monotonically increasing per-path version. At redemption, the fake tool checks that version and commits the write atomically under the same lock. An intervening write invalidates the approval, including an ABA sequence (value changes and then returns to its original bytes).

Both variants consume receipts once; neither is a real credential or a real GitHub writer. The version check is intentionally at the *simulated tool boundary*, not an earlier separate read.

## Reproduce

```bash
cd experiments/khepri/exp420
python -m unittest -v test_state_bound.py
python benchmark.py
```

**Observed locally:** 17/17 unit tests passed. Seeded benchmark `seed=420`, 5,000 cases per domain (SEO, gold), each paired across both policies:

| Synthetic domain | Baseline stale overwrites | Version-bound stale overwrites | Legitimate clean/unrelated writes accepted by both | ABA conflicts rejected by version-bound |
| --- | ---: | ---: | ---: | ---: |
| SEO | 2,966 | 0 | 2,034 | 968 |
| Gold | 2,995 | 0 | 2,005 | 1,024 |

The 10,000 paired cases generate 20,000 redemption attempts. Scenario types are randomly selected with equal nominal probability from clean, intervening write, ABA, unrelated-resource change, and create race. These are *deliberately generated conflicts*, not measurements of production conflict frequency. In this model the version-bound policy rejects all stale attempts and accepts all clean/unrelated writes. The baseline accepts all, including stale overwrites. `results.json` contains exact counts.

## Counterexamples and limitations

- **Counterexample to plan+payload sufficiency:** peer changes `sample.txt` after approval; baseline overwrites peer data despite matching plan and digest.
- **Counterexample to content-equality checking:** peer changes the resource and restores the old bytes (ABA). Only a monotonic version detects this intervening history.
- **Counterexample to global-version locking:** changes to a *different* path should not invalidate this approval. The model uses per-path versions.
- A real implementation needs a trustworthy version source and an atomic conditional write at the actual external tool boundary. Reading version, checking it in the agent, then doing an unconditional remote write would reintroduce TOCTOU.
- Version-only conflict rejection does not automatically reconcile changes. A stale approval must be re-evaluated against fresh content and re-approved, not blindly retried.
- A real GitHub implementation would need branch-head/tree/blob conditional semantics or another transactional mechanism; this toy `FakeStore` is **not** a GitHub API implementation.
- This is a single-process model. No real concurrent network calls, crash recovery, remote authentication, issuer compromise, malicious interpreter code, LLM prompt injection, or adversarial denial of service were tested. The fake store is not durable, and its lock/versions are not distributed.

**Transferable lesson:** authorization must bind not just *who may write what bytes where*, but sometimes also *which observed state the write is based on*. Keep conditional checks and side effects atomic in the actual execution boundary.
