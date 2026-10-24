# Lumen 377 — Disposable regression-input snapshots

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, `sandbox/worker-c`.

## Motivation

Lumen 376's hash-before/hash-after guard detects net changes to regression inputs, but still runs test code in the source checkout. A test with an accidental relative-path write can change the checked-out fixture before the guard detects it. An intervening restore can also defeat the net-drift check.

## Change

Introduced `lumen377_isolated_receipt.py` as an additional, reversible CI diagnostic without replacing the Lumen 376 runner. It copies the explicit manifest of test scripts, modules and fixtures into a new disposable temporary directory **separately for each Python mode**. It then runs `unittest` from that directory, verifies both the copied inputs and source inputs against the initial hashes, and fails closed on test failure, missing inputs, net drift, or symlinked source manifest entries. It disables bytecode generation and removes inherited `PYTHONPATH` from the subprocess environment. Temporary copies are removed automatically.

Added `test_lumen377_isolated_receipt.py` with six deterministic tests: both modes succeed with clean independent copies; a test's relative fixture mutation stays in the disposable copy and is detected; an optimized-only mutation is detected without touching the source; missing and symlinked inputs fail closed; a failing test fails; invalid manifests fail.

Added separate steps to `.github/workflows/lumen-regression.yml` to execute the new tests and full isolated regression alongside the original exact-input receipt, on Python 3.12 and 3.13.

## Verification status

- **Local:** Six tests passed under normal Python and six under `python -O` (12 executions). The local environment used a minimal shim of the Lumen 373 manifest/hash helper because the full GitHub checkout was not locally available. This validates the isolated runner's synthetic behavior, **not** the full repository's actual regression dependencies.
- **GitHub:** The module, tests and workflow were created/updated on the authorized branch, then fetched again by path to confirm they exist. A follow-up change moved the symlink check before content hashing to avoid following potentially out-of-scope manifest links.
- **CI:** A completed GitHub Actions run for the Lumen 377 commits was **not verified** during this cycle. Do not claim that the 79-test regression suite passed in the new isolated runner until its actual CI logs are checked.

## Limitations and next experiment

This is **not an OS security sandbox**, immutable filesystem, independent custody, trusted timestamp, or protection from intentionally malicious code. A test could explicitly use absolute paths or change file permissions; transient mutate-restore activity inside a disposable copy can still evade end-of-run drift checks. Unmanifested dependencies are excluded by design. Source symlinks are rejected before reading, but a malicious concurrent filesystem actor could race file checks; stronger no-follow file-descriptor capture would be a future hardening step.

Next: verify the new CI jobs and inspect their exact receipts. If successful, evaluate whether the older direct-checkout runner can be retired without losing useful cross-checks. For actual adversarial isolation, investigate an OS-level sandbox with enforced read-only mounts rather than presenting a temporary directory as a security boundary.
