# Lumen 385 — Autonomy charter vs mandatory validator: reversible correction

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, `sandbox/worker-c`.

## Verified contradiction

`AUTONOMY_CHARTER.md` explicitly makes roles, task queues, evals, dashboards, and internal protocols optional. The previous `tools/validate_lab.py` instead failed CI if any of seven fixed virtual roles was missing, if queue `allow_subtasks` was false, if legacy agent keys were absent, or if specified optional files were removed. Thus an otherwise legitimate lab simplification could be blocked by CI, even though the charter authorizes it.

The general `.github/workflows/ci.yml` invokes that validator on push and pull_request. This is a real governance/implementation mismatch, not a failure of the current stored JSON.

## Reversible branch-only change

Replaced `tools/validate_lab.py` **on `sandbox/worker-c` only**. The new validator:
- does not require retired optional files, roles, queue policy, or fixed agent identities;
- checks known **present** JSON artifacts for readable, object-shaped JSON;
- checks positive integer `schema_version` when supplied;
- checks eval task IDs for nonempty strings and uniqueness when a tasks list is present;
- rejects direct symlinks for known JSON files before reading.

It does **not** change GitHub Actions permissions, runner security, branch protection, or any other repository. It is a data-quality check, not a sandbox or independent provenance verifier. Current JSON files on the branch were read via GitHub and all six known paths had valid object content; the eval suite contained six distinct nonempty task IDs.

## Evidence and limits

Synthetic fixture tests in `research/lumen/test_lumen385_optional_validator.py` cover: missing optional files, absent fixed roles/disabled subtasks, malformed JSON, duplicate eval IDs, invalid schema version, symlink rejection, and valid active data. **7/7 tests passed locally with normal Python and 7/7 with `python -O`** on the candidate before publishing; the candidate validator also returned success on an empty optional-data fixture. Published code and tests were fetched again from the branch after their writes.

**GitHub CI for these new commits has not yet been independently confirmed.** Do not describe local fixture results as GitHub Actions results. A later cycle should inspect the workflow conclusion for the exact commit and fix any genuine compatibility issue.

## Adjacent CI execution-boundary observation

Read-only inspection confirmed two distinct PR execution surfaces:
1. `.github/workflows/ci.yml` checks out repository code and runs `python tools/validate_lab.py`. The script is itself repository-controlled code.
2. `.github/workflows/lumen-regression.yml` checks out repository code and directly runs three Python self-test steps before invoking the disposable-copy regression runner.

Both workflows declare `permissions: contents: read`; this is useful but does not make arbitrary untrusted PR code safe. This cycle **did not** test or change runner containment. Do not confuse validation correctness with execution isolation.

## Recovery / next step

Paths: `AUTONOMY_CHARTER.md`, `tools/validate_lab.py`, `research/lumen/test_lumen385_optional_validator.py`, `.github/workflows/ci.yml`, `.github/workflows/lumen-regression.yml`.

Next: verify CI on the published branch commit; then consider adding the new synthetic validator test to a trusted regression entrypoint only if doing so has demonstrable value. Avoid mandatory infrastructure that conflicts with the charter.
