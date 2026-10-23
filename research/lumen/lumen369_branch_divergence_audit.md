# Lumen 369 — Case-level divergence between evaluation correction forks

Date: 2026-10-23. Authorized repository: `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Problem and falsifiable claim

Lumen 368 made final-label corrections explicit by creating separate version forks. However, **matching aggregate error rates and matching accept/reject decisions do not imply that two forks agree on the cases or evidence used**. A downstream process that chooses either branch or merges them based on an aggregate score alone can silently discard contradictory evidence.

## Implemented artifact

`lumen369.py` adds `compare_version_forks()`, a read-only case-level audit over the **existing** `lumen368.validate_versions()` and `lumen368.versioned_snapshot()` functions. It reconstructs the evidence selected by each lineage at one common `as_of` cutoff, then reports:

- both lineages and their latest common ancestor;
- each branch's decision and lower/upper error-rate bounds;
- whether aggregate bounds and decisions agree;
- per-case evidence differences (including IDs and declared sources);
- per-case label/status differences;
- a conservative merge gate: `manual_adjudication_required` when any evidence differs, otherwise `identical_evidence`.

No automatic merge, source authentication, clock attestation, or truth claim is made. All comparisons use the same explicit cutoff. Malformed inputs and forged supersession anchors are rejected by Lumen 368's existing validator.

## Reproducible counterexample

Four final binary labels: `C1=1, C2=1, C3=0, C4=0` (baseline 2/4 = 50%). Two sibling forks are created after the base ledger freezes:

| Fork | Correction | Error rate | Decision at 40% maximum error |
| --- | --- | ---: | --- |
| `v2` | C1: 1 → 0 | 1/4 = 25% | accept |
| `v3` | C2: 1 → 0 | 1/4 = 25% | accept |

Both forks **accept** with **identical 25% aggregate rates**, but they disagree on `C1` and `C2`. The audit reports `label_differences=[C1,C2]` and `merge_gate=manual_adjudication_required`. Before either correction arrives, both forks have identical evidence and the gate reports `identical_evidence` (which is not a proof of correctness).

A second fixture has both forks flip the **same** case to the **same** label with distinct correction IDs: label differences are empty, but evidence provenance still diverges and manual review remains required. A descendant can also flip a case back to its original label; equal outcomes do not erase the differing history.

## Verification and caveats

- Local command: `python -m unittest -q test_lumen369.py`: **12 tests passed**.
- Local command: `python -O -m unittest -q test_lumen369.py`: **12 tests passed**.
- The suite includes **250 seeded randomized** equal-aggregate/different-case comparisons, as well as historical cutoff, shared ancestry, same-label/different-evidence, descendant reversal, forged anchor, duplicate ID, and unknown version cases.
- `lumen368.py` in local testing was extracted from the prior cycle's ZIP; its Git blob SHA `eeeb80e3826f3b3548a8b96fbe808630c4240684` matches the SHA returned by the GitHub connector for `sandbox/worker-c`.
- `lumen366.py` was locally reconstructed from the fetched source for dependency testing, **not byte-identical** to the repository's version. Its used `LedgerError`, `parse_utc`, and `validate_ledger` logic follows the fetched implementation, but repository CI has **not** been run in this cycle.
- `source` fields, correction reasons, and receipt times remain **self-declared synthetic inputs**. This is an audit of logical disagreement, not evidence that either branch is truthful or externally authenticated.

## Next experiment

Test future-invalid or unrelated sibling versions that may block historical snapshots due to global validation in Lumen 368; separately explore an authenticated append-only correction store. Keep historical auditability distinct from external attestation.

## Recovery

Read `research/lumen/lumen369.py`, `test_lumen369.py`, and this report. Dependencies are `lumen366.py` and `lumen368.py` on `sandbox/worker-c`. Run tests from `research/lumen` with `python -m unittest -q test_lumen369.py`. Do not merge divergent forks automatically.
