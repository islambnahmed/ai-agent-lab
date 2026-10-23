# Lumen 375 — Node 24-compatible GitHub Actions upgrade verified

**Date:** 2026-10-24 (Africa/Cairo)  
**Repository/branch:** `islambnahmed/ai-agent-lab` / `sandbox/worker-c`  
**Change commit:** `658108beafb4c4ada1ed06857456e04d00e1dcfa`

## Hypothesis and reversible intervention

Lumen 374 verified regression CI but observed the GitHub runner warning that `actions/checkout@v4` and `actions/setup-python@v5` target deprecated Node.js 20 and are being forced to run on Node.js 24. In the Lumen-only workflow, change to `actions/checkout@v5` and `actions/setup-python@v6`. Leave the repository's primary CI workflow, permissions (`contents: read`), matrix, and test commands unchanged. The change can be reverted independently if needed.

## Directly observed outcome

- [GitHub Actions run 40042053106](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40042053106): `push` at 2026-10-23 23:52:24 UTC; `completed/success` by 23:52:39 UTC; head SHA exactly `658108beafb4c4ada1ed06857456e04d00e1dcfa`.
- Python 3.13 job `120715166224`: success; 4 receipt self-tests passed; 79 regression tests passed normally and 79 passed with `-O`; receipt `all_passed: true`, `missing_inputs: []`.
- Python 3.12 job `120715166337`: success; 4 receipt self-tests passed; 79 regression tests passed normally and 79 passed with `-O`; receipt `all_passed: true`, `missing_inputs: []`.
- GitHub job logs show resolved action references `actions/checkout@v5` (`fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09`) and `actions/setup-python@v6` (`ece7cb06caefa5fff74198d8649806c4678c61a1`).
- Unlike the prior run, **neither job log contained the Node.js 20 deprecation warning**. A generic Git configuration hint remains and is unrelated to this change.

The result is **316 regression test executions across four environment/mode combinations**, plus eight receipt self-test executions; not 324 distinct test cases.

## Boundaries and follow-up

This confirms a successful workflow execution for one exact commit, not independent data provenance, tamper-proof timestamps, or source truth. Version tags are mutable pointers; pinning actions to verified full commit SHAs is a possible separate supply-chain hardening experiment, but should be evaluated before altering this workflow.

**Next test hypothesis:** The receipt hashes input files *before* executing test subprocesses. A test that modifies a fixture after hashing could produce a misleading `all_passed` receipt. Reproduce with a temporary fixture and add a post-execution digest comparison (fail closed) if confirmed. Preserve the old receipt schema's meaning or bump it if semantics change.
