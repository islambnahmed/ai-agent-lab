# Lumen 379 — Empirical boundary contract for disposable test snapshots

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Question

Does Lumen 377's disposable-input copying actually constrain test code, or only protect against accidental relative-path modifications? Lumen 378 explicitly recommended adversarial evidence rather than more receipt wrappers. This cycle tests the boundary and keeps the existing runner unchanged.

## Controlled experiment

Added `research/lumen/test_lumen379_boundary_contract.py`. Every fixture, including the simulated checkout and all modified files, is created beneath the test's own `tempfile.TemporaryDirectory`; no real repository or unrelated user data is modified by the synthetic tests.

| Scenario | Expected and locally observed | Implication |
| --- | --- | --- |
| Relative write to manifested snapshot input | Receipt fails; original fixture unchanged | Copying and hash comparison work for this limited case. |
| Absolute write to an **unmanifested synthetic checkout** file | Receipt passes, yet marker in synthetic checkout changes | Copied working directory is not a filesystem access boundary; unmanifested files are invisible to the hashes. |
| Temporary write then restore to a **manifested synthetic source** file | Receipt passes, source restored | Before/after hashing cannot detect transient changes between sampling points. |
| Synthetic environment variable passed to child | Child sees the synthetic value; receipt passes | Subprocess inherits ambient environment (except explicitly removed PYTHONPATH); no environment isolation is provided. |

All four cases passed as contract tests locally under ordinary Python and `python -O` (8 test-method executions in two separate unittest runs). The tests **pass when the documented limitations are reproduced**; their passing is not evidence of OS-level containment. Local execution used a reconstructed copy of the Lumen 377 runner and its manifest/hash helper based on the repository sources; the new CI step is intended to check against the actual repository dependencies.

## Decision

**Do not describe disposable snapshots as a sandbox.** Keep them for accidental relative-path mutation protection and fail-closed manifested-input drift detection. Do not claim that they isolate file-system writes, transient access, ambient environment, or provenance. Do not add another receipt wrapper.

Added the four synthetic boundary tests to the existing Python 3.12/3.13 CI workflow, without changing security settings, permissions, or the core runner. The new CI workflow step must pass before the repository-version verification is considered complete.

## Remaining risk and next experiment

If running untrusted tests becomes necessary, a separate, explicitly authorized OS-level sandbox with a read-only source mount, restricted filesystem access, scrubbed environment, and no network is needed; this cycle did **not** implement or validate one. Evaluate a real enforced isolation mechanism only if its security and compatibility costs justify it. A clean checkout and copied inputs do not constitute independent provenance.

## Evidence and recovery

- Test: `research/lumen/test_lumen379_boundary_contract.py`
- CI: `.github/workflows/lumen-regression.yml`
- Test-file commit: `79e2a6270f8d5c0e95e47a89ab583375a25312c8`
- CI-step commit: `df0f055044e34871f69e075f4072909f8fd3e31e`
- CI outcome: **verified** on workflow-step commit `df0f055044e34871f69e075f4072909f8fd3e31e` in [GitHub Actions run 40059712551](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40059712551). Both Python 3.12 and 3.13 jobs completed successfully. Job logs independently show 4/4 new boundary contract tests, 7/7 receipt tests, 6/6 isolated-runner tests, and 79/79 full regression tests in each of normal and optimized modes; both receipts had `all_passed: true`, `source_drift: []`, and `snapshot_drift: []`. This verifies behavior of the repository code, **not** OS-level sandboxing.
