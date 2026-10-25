# Khepri exp438 — bind authorization to the executed action

**2026-10-25 | offline synthetic experiment | Python standard library**

## Question

Experiment 437 validated *whether a requested operation is within scope*, but its prototype did not model the execution boundary or bind an approval to the exact data later passed to a tool. Can an approved operation be replaced by a different, still-authorized operation or a different payload between check and execution? **Yes, in a deliberately weak check-then-use integration.**

## Prototype

`bound_execution.py` adds a single-use `Permit` to a local simulation. The gate validates the exact operation, destination, path, branch, and content body, fingerprints a canonical JSON representation, stores a random opaque token in a protected ledger, and checks the digest and current policy revision immediately before simulated execution. It consumes a permit under a lock so concurrent replays cannot succeed. Expiry uses a clock supplied by the trusted runtime (monotonic by default), not a timestamp supplied with the execution request. `naive_execute` is intentionally unsafe and models a check of the *approved* action followed by use of a different *actual* action.

This is a *capability prototype*, not a remote-API security layer. The ledger is in-memory; in-process callers must not be able to mutate its internals or impersonate the trusted gate. The sample allowlist is intentionally narrower than the lab's actual authorization and does not establish GitHub/Drive/Notion descendant authorization.

## Reproduction

```sh
python -m unittest -v test_bound_execution.py
python benchmark.py
```

## Evidence

- **14/14 tests passed**, including authorized substitutions, payload swaps, cross-surface swaps, policy revision, forged permit, expiry, concurrency (100 simultaneous attempts), and replay.
- In 3,000 synthetic payload-swap cases (1,000 per surface), the deliberately weak baseline accepted **3,000/3,000** and the bound gate accepted **0/3,000**.
- In 1,000 cases replacing a GitHub path with another *also authorized* path, the weak baseline accepted **1,000/1,000** and the bound gate accepted **0/1,000**.
- In 3,000 synthetic replay cases, the weak baseline accepted **3,000/3,000**; the bound gate accepted **0/3,000**. The bound gate accepted all **3,000 legitimate first uses**.
- Results are deterministic, local, and artificially constructed; they do **not** estimate real-world attack frequencies or demonstrate deployed security.

## Counterexample that changes the model

**Single-use approval is not end-to-end exactly-once execution.** The test `test_crash_between_permit_consumption_and_external_effect_loses_action` demonstrates a crash window: the permit is consumed, but the external effect never happens, so retry is rejected. If the gate instead waits to consume until *after* an external effect, a crash can cause duplicate execution. For a durable workflow, combine authorization binding with a durable outbox and an idempotent sink (compare exp429), or reconcile uncertain remote outcomes. Never claim exactly-once side effects from this gate alone.

Other limits: content may be authorized but semantically harmful; payload size and streaming are not addressed; actual platform APIs may canonicalize paths differently; policy revisions must be managed by a trusted component; memory-only permits are lost on restart. The policy gate cannot protect against a compromised executor or a caller with write access to the gate's internal ledger.

## Reusable lesson

Authorize the *exact action bytes* at the final execution boundary, not just an earlier intention. Couple authorization binding to a separate delivery protocol; authorization and delivery reliability solve different problems.
