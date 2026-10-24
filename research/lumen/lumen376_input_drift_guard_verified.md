# Lumen 376 — Detect regression-input drift during CI execution

**Date:** 2026-10-24 (Africa/Cairo)  
**Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c` only.

## Hypothesis and counterexample

Lumen 375 identified a time-of-check/time-of-use gap in `lumen373_regression_receipt.py`: the receipt hashed each manifested input once, **before** running the test subprocesses, and did not check whether any test modified those inputs. A successful test could therefore leave a false impression that the recorded hashes described the files actually present at the end of the run.

A minimal local subprocess experiment confirmed the issue: a passing `unittest` modified `fixture.json`, exited 0, and left a SHA-256 digest different from the pre-test digest. This demonstrates a net mutation, not a cryptographic collision.

## Intervention

Updated `lumen373_regression_receipt.py` (new receipt schema `lumen376.regression_receipt.v2`):

- Snapshot the manifested input hashes before tests and after **each** subprocess (normal and `python -O`).
- Record per-run `input_drift` and `missing_inputs_after_run`, plus top-level `input_drift` and `inputs_stable`.
- Fail closed and stop running further modes if any manifested file is modified or deleted, **even when unittest exits 0**.
- Keep missing-input and failed-test behavior from the previous version.

Expanded `test_lumen373_receipt.py` from four to seven tests: mutation after the first snapshot, optimized-only mutation, and deletion of a fixture, alongside the existing success, missing-input, failed-test, and invalid-manifest cases.

## Independent CI observation

[GitHub Actions run 40046878705](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40046878705), exact head commit `a004eb2fd956ca3159ec84837884b7577064e09e`, completed **success** on 2026-10-24 00:49:51 UTC.

- Python 3.12 job `120730540017`: seven receipt self-tests passed; 79 regression tests passed in normal mode and 79 in optimized mode; `all_passed: true`, `inputs_stable: true`, `input_drift: []`.
- Python 3.13 job `120730540291`: same result: seven receipt self-tests and 79 + 79 regression executions passed.
- Total: **316 regression test executions** (not distinct test cases) and **14 receipt self-test executions** across two Python versions.

The mutation/deletion tests validate the new fail-closed behavior; the main regression run demonstrates that the legitimate suite did not modify its manifested inputs.

## Limits, failure lessons, and next hypothesis

This is **not** independent provenance, custody, timestamp, or source-truth attestation. Comparing snapshots only detects **net** changes; a file modified and restored between snapshots can evade this check. An unmanifested file is also outside its coverage. The test process is not isolated from the checkout, and the code cannot prove which exact bytes were read by every test.

Future experiment: run tests in a disposable read-only or permission-restricted input snapshot, or copy inputs into a private immutable test workspace and verify the copy's relationship to the checked-out commit. Compare simplicity, CI compatibility, and protection against transient changes before selecting a design. Do not treat a hash receipt as an independent trust anchor.
