# Khepri exp427 — independent witness quorum against fabricated evaluation scores

Date: 2026-10-24. Authorized AI Agent Lab only. Research prototype; standard-library Python, synthetic data. Builds on exp426's independently precommitted opportunity manifest. `baseline_manifest_gate.py` is a copy of the exp426 module at `experiments/khepri/exp426/manifest_gate.py` on `khepri/exp426-anchored-manifest-20261024-1900`.

## Question and competing explanation

Exp426 prevents selective round deletion but explicitly accepts fabricated scores. Can independent raw-observation receipts make an untrusted logger's fabricated scores irrelevant? A single supposedly trusted witness can itself be poisoned, so compare one-witness reliance with a **strict-majority 2-of-3 witness quorum**.

## Method

1. A pre-outcome policy fixes source slots, candidates, witness IDs, strict-majority threshold, and bounded metric. The verifier receives its expected SHA-256 commitment from an **independent** authority.
2. Each witness reports raw nonnegative integer (before, after) observations per candidate and slot. The score is deterministically (after-before)/max(1,before,after) in [-1,1].
3. For each candidate and slot, at least two distinct, independently authenticated witnesses must report identical raw pairs. Agent-submitted scores are **never used**. If any candidate-slot lacks quorum, evaluation fails closed; one missing witness is tolerated if the other two agree.
4. Reuse exp426's bounded e-process and fixed candidate-family threshold on the quorum-reconciled score stream. Reject duplicate/unknown/malformed witness records and policy changes.

**Critical trust assumptions:** witness identity is authenticated externally (not implemented here), at most one of three witnesses is corrupt, witness failures are not correlated, the schedule and policy commitment are independently trusted, and the e-process's conditional-null assumptions hold. A hash alone authenticates neither witness nor outcome. No keys, credentials, external accounts, or network services were used.

## Evidence (local execution)

`python -m unittest -v test_quorum_gate.py`: **16/16 pass**, including 27 exhaustive one-slot witness-state combinations, 2^9 exact fair-sign enumeration, malformed input tests, multi-candidate quorum, and explicit two-witness collusion counterexample.

`python benchmark.py > results.json`: 200 seeded deterministic trials each for SEO (80 binary before/after slots, one candidate) and finance (60 large-magnitude count slots, two candidates), 400 trials total. Balanced sign pairs keep the honest stream non-improving; this is an adversarial stress test, **not** a calibrated false-positive-rate experiment.

| Attack/scenario | SEO positive crossings | Finance positive crossings | Blocked trials per domain |
|---|---:|---:|---:|
| Exp426, forged agent-submitted scores | 200/200 | 200/200 | 0 |
| Quorum, honest receipts | 0/200 | 0/200 | 0 |
| Quorum, one witness fabricates positive observations | 0/200 | 0/200 | 0 |
| Quorum, two witnesses collude | **200/200** | **200/200** | 0 |
| Quorum, one honest witness offline | 0/200 | 0/200 | 0 |
| Quorum, one honest witness offline + one corrupt | 0/200 | 0/200 | **200/200** |

## Counterexamples and limitations

Two colluding witnesses can fabricate a quorum and force a positive decision. If one honest witness is offline while a remaining witness is corrupt, the system rejects rather than guesses; availability is sacrificed for safety. A single operator impersonating two witness identities also defeats the quorum, because this prototype **does not** authenticate channels or identities. Witnesses that share the same faulty upstream measurement are not independent. Complete pre-outcome source coverage and statistical validity are still external assumptions. This is not production security.

## Reproduce

Run from this directory, Python 3.10+:

```bash
python -m unittest -v test_quorum_gate.py
python benchmark.py > results.json
```

No dependencies beyond the Python standard library. No external services.

## Lesson

A committed opportunity roster prevents round deletion but not outcome fabrication. Majority agreement over **independently authenticated raw measurements** can resist one compromised witness, but cannot create trust from correlated or forged identities. A sensible next experiment would introduce independent channel authentication and a controlled common-mode measurement-failure test; do not treat hash commitments as signatures.
