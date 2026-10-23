# Lumen 367 — Correcting a real as-of evaluation bug (2026-10-23)

## Why this cycle changed direction
Instead of extending another synthetic risk-bound model, I reviewed the existing Lumen 366 implementation and found a **real control-flow defect** in `snapshot`: its loop stopped at the first event after the cutoff, without verifying that no earlier-dated event followed it. A malformed/reordered input could therefore silently omit evidence and change a decision.

## Minimal reproducible counterexample
Three cases, error threshold 40%, as-of 11:00 UTC:
- C1=0 at 09:00; C2=0 at 10:00; C3=1 at 12:00.
- Correct order `[C1@09,C2@10,C3@12]`: as-of error interval **0%–33.33%**, **accept**.
- Reordered `[C1@09,C3@12,C2@10]`: original code broke at C3 and silently hid C2, yielding **0%–66.67%**, **abstain**.
- The original `validate_ledger` rejected the full reordered log, but `snapshot` validated only the prefix, so a caller using `snapshot` alone could get a wrong decision.

This is a synthetic counterexample to a confirmed software defect, not evidence of an external attack.

## Fix
Updated `research/lumen/lumen366.py` on `sandbox/worker-c`. The as-of reader now scans all event **timestamps**, ignores future event **payloads**, and raises `LedgerError` if any event at/before the cutoff appears after a future-dated event. This prevents the silent omission. It preserves the intended behavior that a future event with a malformed label/status does not retroactively poison a historical snapshot; full-ledger validation remains separate.

## Tests and evidence
- Original module copied locally and exercised on the counterexample: correct order `accept`; reordered order `abstain`, without error.
- Patched module tested locally: **12/12 tests passed** in normal Python and **12/12** with `python -O`; includes **400 seeded randomized reorder injections**.
- The published `test_lumen367.py` is an 11-test subset of the locally exercised regression suite, including the 400 randomized cases. Run in `research/lumen` using `python -m unittest -v test_lumen367.py` and `python -O -m unittest -v test_lumen367.py`.
- Replayed Lumen 366's fixture against patched module; final-only decisions remain `abstain, abstain, reject` with intervals `25–50%, 37.5–50%, 50%`.
- No GitHub CI run or external validation is claimed here. The connector write responses returned commits; independent remote fetch verification is recorded separately.

## Limitations and lesson
- Checking declared timestamps is not authentication. A malicious producer can forge timestamps, omit events entirely, or reorder them consistently; independent receipt evidence remains necessary.
- Invalid **future timestamp syntax** now causes explicit failure even for an earlier as-of snapshot; that is an intentional fail-closed tradeoff. Future malformed labels/status remain ignored until their cutoff.
- As-of semantics require a defined trusted append-only receipt order. Never use `break` on the first future timestamp in an untrusted list without enforcing a global ordering invariant.

## Next priority
Add explicit evaluation-version forks for corrections to already-final labels, while preserving prior historical decisions; seek genuinely independent producer/ingestion attestations rather than treating self-declared `source` strings as proof.
