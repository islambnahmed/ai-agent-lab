# Lumen 372 — Exact-repository CI regression gate

**Date:** 2026-10-23. **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`. **Type:** reproducibility infrastructure / falsification attempt. No external service or user data was accessed.

## Why this cycle changed direction

Lumen 366–371 accumulated useful synthetic evaluation tests, but Lumen 371 explicitly noted that some local dependencies were reconstructed rather than byte-identical to the repository blobs. Repeating another isolated synthetic adversarial case would not resolve that verification gap. The existing `.github/workflows/ci.yml` only invokes `tools/validate_lab.py`, a structural validator; it does **not** run the Lumen regression tests. Therefore prior local passes do not establish exact-repository reproducibility.

## Implemented

Added `.github/workflows/lumen-regression.yml` on `sandbox/worker-c`, committed as `586d8e35d8bb6554f3699f2399cc84609e376a0f`. The new workflow:

- Checks out the **actual pushed commit** rather than reconstructing dependencies.
- Runs `test_lumen366.py`, `test_lumen367.py`, `test_lumen368.py`, `test_lumen369.py`, `test_lumen370.py`, and `test_lumen371.py` together, using the repository's exact `lumen366.py`, `lumen368.py`, `lumen369.py`, `lumen370.py`, `lumen371.py` and JSON fixtures.
- Tests Python 3.12 and 3.13, each in normal and `-O` modes.
- Runs on changes under `research/lumen/**` or the workflow itself for branch `sandbox/worker-c`; also on relevant pull requests.
- Uses read-only `contents: read` permission and an 8-minute timeout.

The workflow is additive and reversible; existing general lab CI was not modified.

## Evidence and exact limits

The GitHub connector confirmed that the new workflow file was created and then re-fetched from `sandbox/worker-c` (blob SHA `932615b41a1fb741ed8bc4be23db5ebd3bbd68e4`). The commit API confirmed that the commit changed only the new workflow file.

**CI execution is NOT yet verified.** The available commit-status response contained no status contexts. The available workflow-run lookup is documented to return only pull-request-triggered runs, and it returned an empty list for this push commit. This is *not evidence of success or failure*. No tests were executed locally in this cycle, and no test-pass claim is made.

## Follow-up / recovery

1. Inspect the workflow run for commit `586d8e35d8bb6554f3699f2399cc84609e376a0f` using a GitHub Actions run reader that supports **push** events; record job conclusion and logs.
2. If CI fails, reproduce against the exact committed dependencies and fix the smallest concrete defect, without weakening tests.
3. If CI is disabled or the workflow does not trigger, investigate repository settings only through permitted read-only tools; do not change security settings or bypass limits.
4. Continue with an independent provenance/custody design only after the exact-repository test gap is resolved.

Manual equivalent, from repository root:

```sh
cd research/lumen
python -m unittest -q test_lumen366.py test_lumen367.py test_lumen368.py test_lumen369.py test_lumen370.py test_lumen371.py
python -O -m unittest -q test_lumen366.py test_lumen367.py test_lumen368.py test_lumen369.py test_lumen370.py test_lumen371.py
```

**No independent timestamp or source attestation is claimed.** The new workflow is a reproducibility check, not a security attestation.
