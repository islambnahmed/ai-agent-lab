# Khepri exp441 — adversarial ACK/effect ordering audit

**2026-10-25 | local, deterministic SQLite fault injection | no external effects**

## Question

Exp440 showed duplicate-effect suppression under a trusted caller. Does its API enforce delivery safety when an ACK arrives before the sink effect, or when a claim is fabricated? Can a separate-database wrapper preserve crash recovery while rejecting those transitions?

## Reproduced baseline counterexamples

1. Enqueue, claim, then ACK marks an operation **done with zero sink effects**. The original ACK never checks for a sink receipt. A premature ACK loses the job.
2. Calling apply_sink with a fabricated Claim creates an effect for an operation never recorded in the outbox. The original sink checks digest self-consistency, not outbox provenance.

These are trust-boundary counterexamples to the *simulation API*, **not** vulnerabilities established in GitHub, Notion, or Drive. Exp440 explicitly assumed a trusted caller.

## Prototype

The new verified_delivery.py wraps the original exp440/durable_delivery.py using **separate outbox and destination SQLite files**. It verifies that a claim is current, unexpired, and bound to an immutable queued payload before dispatch. Its ACK requires a matching durable sink receipt **and** one matching effect; it checks and updates the outbox under a transaction to avoid claim-generation races.

The sink remains independently idempotent by stable operation ID. If a crash occurs after effect but before ACK, a new worker retries and receives a duplicate receipt rather than repeating the effect.

## Reproduce

From the repository root, with Python 3.10+ and standard library only:

    cd experiments/khepri/exp441
    PYTHONPATH=../exp440:. python -m unittest -v test_durable_delivery test_verified_delivery
    python benchmark.py

The parent exp440 files are inherited on this branch; no shared main files were changed.

## Verified local evidence

- **27/27 tests passed**: 15 exp440 tests plus 12 new adversarial tests.
- Two baseline counterexamples reproduced and rejected by the wrapper.
- **8,000 randomized transitions** (100 seeds × 40 steps × 2 families) included fabricated claims, modified payloads, premature ACKs, lease reclaims, and process restarts. Every completed job had exactly one effect and all trials converged.
- **400 crash-before-ACK operations** (200 SEO + 200 gold) across two SQLite files: 400 first effects, 400 suppressed retries, 800 rejected forged/altered dispatch attempts, **zero duplicate effects**, and **zero pending jobs** after recovery.
- Further tests show a receipt without an effect and an effect without a receipt cannot authorize ACK.

## Limits

- The wrapper assumes a trusted dispatcher, trusted sink readback, atomic receipt/effect storage, and honest now. It is not cryptographic authentication and does not implement exp439 authorization or real service adapters.
- Dispatch verification and a remote effect cannot be atomic across a network. Leases may expire mid-flight; remote idempotency remains essential.
- Real services may not support idempotency or read-after-write confirmation. In that case use an explicit uncertain-outcome/reconciliation state, not blind retries of irreversible operations.
- Receipt retention, cancellation/revocation, partitions, clock drift, and malicious database access remain open concerns.

**Lesson:** enforce safety invariants at transition boundaries. Testing only the expected call order hides premature ACK and unbacked-effect failure modes.
