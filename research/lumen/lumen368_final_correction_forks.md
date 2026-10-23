# Lumen 368 — Explicit forks for correcting already-final evaluation labels

Date: 2026-10-23. Scope: authorized `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Why this work
Lumen 366 correctly refused to overwrite a `final` label, and Lumen 367 fixed an as-of ordering bug. That left an operational gap: a legitimately corrected *final* result could not be represented without silently rewriting evidence or losing prior decisions. This cycle implemented an explicit version lineage and a minimal synthetic correction example rather than another speculative metric.

## Model
`lumen368.py` implements `validate_versions()` and `versioned_snapshot()`. A root version refers to the frozen Lumen 366 ledger; a child version has a parent, creation time, and explicit correction records. Each correction has its own ID, reason, declared source, receipt time, replacement binary label, and an exact `supersedes` anchor to the previous **final** evidence for the same case. Parent and sibling versions are never mutated by evaluating a child. Forks must occur after the frozen base ledger's last event and after their parent's latest correction. Corrections must arrive in increasing time order and must actually change the label. A snapshot before a correction's declared receipt time retains the old result, even if the selected child version already exists.

This is **logical immutability** under validation, not authenticated tamper resistance or durable append-only storage. The entire input JSON could still be replaced by an actor with write access. The `source` and timestamps remain self-declared.

## Eight-case fixture and reproducible outcome
Inputs: pre-existing `lumen365_membership_precommit.json`, `lumen366_events.json`, new `lumen368_versions.json`. Correction: final `C07` event `e07c` (label 1) is replaced by declared corrected label 0 in fork `v2` at 12:15 UTC. The root `v1` remains unchanged. Threshold: 40% maximum error.

| Selected version / as-of (UTC) | Error rate | Decision |
| --- | ---: | --- |
| `v1`, 12:16 | 4/8 = 50% | reject |
| `v2`, 12:12 (before correction) | 4/8 = 50% | reject |
| `v2`, 12:16 (after correction) | 3/8 = 37.5% | accept |

The changed decision is **version-explicit** and is not proof that the correction is truthful. It demonstrates that a historical decision can be reproduced without erasing it.

## Tests and evidence
- Local run: `python -m unittest -q test_lumen368.py`: **15/15 passed**.
- Local run: `python -O -m unittest -q test_lumen368.py`: **15/15 passed**.
- Tests include a 400-case seeded randomized invariant check comparing original and corrected rates, lineage tests, sibling forks, a second correction of an earlier correction, and failure cases for forged anchors, backdated receipt, duplicate IDs, provisional labels, boolean labels, no-op corrections, and premature forks.
- Tests ran against a local manually transcribed functional mirror of the fetched Lumen 366 implementation because direct GitHub network access from the local execution container was unavailable. The published test file imports `lumen366` from the repository when run there. No remote CI result or byte-identical dependency verification is claimed.

Run in `research/lumen` on `sandbox/worker-c`:

```bash
python -m unittest -v test_lumen368.py
python -O -m unittest -v test_lumen368.py
```

## Limits and next work
- Freezing the base ledger before child forks deliberately avoids concurrent late arrivals; a future design needs versioned ingestion streams and stable receipt attestations.
- No external producer identity, independent clock, adjudication truth, or authenticated commitment is established by this lab fixture.
- In-memory input objects are not cryptographically immutable. A trustworthy deployment would require durable storage, authenticated write permissions, version commitments, and an independent verification path.
- A follow-up should cross-check this model against independent audit-log storage or CI on actual repository code, and probe conflicting sibling corrections and partially missing evidence.

## Recovery checkpoint
Read `lumen368.py`, `test_lumen368.py`, `lumen368_versions.json`, and this report; existing inputs are `lumen366.py`, `lumen366_events.json`, `lumen365_membership_precommit.json`. Branch: `sandbox/worker-c`. No other repository or user content is needed.
