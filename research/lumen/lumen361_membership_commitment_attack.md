# Lumen 361 — Membership commitments and the self-signed provenance trap (2026-10-23)

## Question and result
Can an auditor accept a false favorable AI-agent risk estimate after an attacker changes which entities an aggregate covers, without changing aggregate values? **Yes** when membership provenance is not independently anchored.

Six canonical entities A–F have true errors A=1, B=0, C=0, D=1, E=1, F=0: **3/6 = 50%**. Seven overlapping OR/COUNT aggregates sharply identify exactly three errors. Changing one group `g2` from membership `{B,C}` to `{A,D}` while keeping `COUNT=0` yields a self-consistent but false sharp bound of **1/6 = 16.67%**. A 25% maximum-error acceptance rule flips from rejection to false acceptance.

| Mode | Sharp errors | At 25% threshold |
| --- | --- | --- |
| Authentic groups | 3/6 = 50% | Reject |
| Tampered membership, no independent anchor | 1/6 = 16.67% | False accept |
| Tampered report checked against original trusted snapshot | Rejected: `g2: membership/kind mismatch` | No decision |
| Attacker supplies both changed snapshot and matching digest | 1/6 = 16.67% | False accept |

## Method
`lumen361.py` creates a canonical JSON snapshot of entity IDs, group names, types and memberships, plus a frame version. It excludes observed values. A SHA-256 digest must be **independently anchored before outcomes**. On audit, check the canonical snapshot against that separately controlled digest, reject membership/type/group-set changes, then run `lumen360.robust_bounds` with an optional budget of corrupted aggregate **values**.

**Critical limitation:** The implementation verifies equality with a *caller-supplied* digest; it cannot verify that the anchor is independent or predates outcomes. A self-signed digest, even if cryptographically correct, is no provenance evidence. Timestamps in an attacker-controlled record do not establish precedence.

## Verification
Local standard-library prototype: **17/17 unit tests passed**, including **250 deterministic random cases for each of k=0 and k=1**, or **500** audited-vs-base solver comparisons. Seed 361. Tests cover canonicalization, digest mismatches, group membership/kind/set edits, frame changes, malformed inputs, value-corruption budgets, and the successful self-signed forgery. Command: `python -m unittest -v test_lumen361`.

Files: `research/lumen/lumen361.py`, `research/lumen/test_lumen361.py`. The locally checked ZIP also contains `lumen360.py`, `results.json`, the test log, report, and SHA256SUMS.

## Limitations and next work
Binary outcomes, OR/COUNT aggregates, exponential exact solver, synthetic examples only. No proof of real-world performance, independent notarization, correct semantic identity mapping, or collusion resistance. Membership corruption is **rejected**, not tolerated; `max_corrupt_values` tolerates values only. Next: partially attested memberships and sharp bounds under bounded uncertain memberships, with explicit independent-anchor assumptions.
