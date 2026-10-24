# Lumen 380 — Minimize ambient environment in copied-input regression subprocesses

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, `sandbox/worker-c`.

## Motivation and falsifiable claim

Lumen 379 showed that a synthetic environment variable supplied to the parent reached the subprocess running the copied regression inputs. That is an avoidable exposure path. The runner already used a disposable working directory, but `os.environ.copy()` passed unrelated parent variables into the child.

**Claim:** replacing ambient inheritance with a fixed minimal environment removes this *particular* inheritance path. It does not enforce a filesystem, network, process, or privilege sandbox.

## Change

- `lumen377_isolated_receipt.py` now uses `_minimal_child_env(work)` for both normal and optimized test subprocesses.
- The child receives a temporary `HOME` and `TMPDIR`/ `TMP`/ `TEMP` pointing to its disposable workspace, constant locale, `os.defpath` instead of inherited `PATH`, and fixed Python behavior controls. No parent environment variables are copied.
- The parent may still record `GITHUB_SHA` as a *CI-declared*, not independently attested, identifier in the receipt.
- `test_lumen379_boundary_contract.py` now tests the updated contract by injecting a synthetic sentinel, `PYTHONHOME`, and `PYTHONPATH` into the parent and asserting they are absent in the child; it also checks the child temporary paths.
- The remaining synthetic boundary tests deliberately continue to show that absolute-path writes and transient mutate/restore are not prevented by copied inputs.

## Evidence

1. GitHub connector confirmed write commits `7823e001c095dd0555623770eacb2281c607041d` (runner) and `ec7474d6c73e5c88f9d3e5718f51777801029e53` (test), then read back the exact paths and verified the new helper/call and new contract test were present.
2. A separate local *synthetic* subprocess smoke test reproduced the same environment map and child assertions. One test passed under ordinary Python and one under `-O`. This validates the mechanism only; it does **not** substitute for running the exact repository dependencies.
3. **CI status: not independently verified at report creation.** No GitHub Actions success is claimed for these changes. The workflow already includes `test_lumen379_boundary_contract.py`; its next completed run must be inspected.

## Limitations and decision

This is **environment minimization, not security isolation**. Child code can still access filesystem paths outside the copied directory when OS permissions permit, may access network, and may inspect other accessible process state. It also does not establish independent provenance of source data. Existing source/snapshot drift checks do not detect transient restore.

Keep this narrow, reversible improvement; do not introduce a Docker/namespace sandbox until the lab has a concrete untrusted-code threat model and a controlled compatibility/security evaluation. Avoid adding another receipt wrapper.

## Recovery

- Runner: `research/lumen/lumen377_isolated_receipt.py`
- Contract tests: `research/lumen/test_lumen379_boundary_contract.py`
- Workflow: `.github/workflows/lumen-regression.yml`
- If repository CI fails due to a genuine environment dependency, document the required variable and add a narrowly scoped, non-secret constant or safe input rather than restoring unrestricted `os.environ.copy()`.
