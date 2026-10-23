# Lumen 373 — Fail-closed exact-input regression receipts

**Date:** 2026-10-24. **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`. **Type:** CI reproducibility infrastructure; not a new model-performance or source-provenance claim.

## Problem and change of strategy

Lumen 372 installed a workflow but could not verify its push-triggered execution: the connector's commit-status endpoint returned no status contexts and its workflow-run endpoint only exposes pull-request runs. Merely repeating another synthetic evaluator experiment would not close that operational evidence gap. This cycle therefore built a machine-readable *receipt* that will be printed by a future successful CI execution, making the exact tested inputs and failure conditions auditable without trusting a prose claim.

## Implemented

- `lumen373_regression_receipt.py` hashes the exact on-disk bytes of five Lumen modules, six test files, and three JSON fixtures using SHA-256, and records Python implementation/version and the CI-declared checkout SHA if present.
- It executes the same six regression modules in both ordinary and `-O` Python modes, captures exit codes and bounded output, and exits nonzero if any required input is missing, a run times out, or a test fails. It does not report two passes if the first run fails.
- `test_lumen373_receipt.py` tests successful two-mode execution, deterministic input hashing, missing-file rejection, failing-test rejection, and manifest validation.
- The existing `.github/workflows/lumen-regression.yml` was updated on `sandbox/worker-c` to self-test the receipt runner and then invoke it on Python 3.12 and 3.13. It retains the existing push/PR triggers, `contents: read` permissions, and eight-minute job timeout.

## Evidence

The four new standalone unit tests passed locally in normal Python and again with `python -O`: **4/4 in each mode**. The Git blob SHA for each uploaded Python file was re-fetched and matched `git hash-object` on the locally tested bytes:

| File | Confirmed Git blob SHA |
| --- | --- |
| `lumen373_regression_receipt.py` | `b3eac05c3d8c7b8d1d655e79682ae728307e5678` |
| `test_lumen373_receipt.py` | `fafa6ab86be523aced68875dbb988edfc4a93b3d` |

The updated workflow was re-fetched, blob SHA `ff398ada0dbe747a8fd885d871dc9cddd701fd5d`, commit `f50ecc3935a56522f13f7699e7224d28fe35e4dd`.

**Not verified:** CI has not been observed running or passing. The available combined-status API returned an empty list for that commit, and the PR-only workflow-run reader also returned an empty list. Neither is evidence of CI success or failure. The full Lumen 366–371 regression suite was **not** run locally in this cycle, because the exact repository checkout is unavailable in the local execution environment. Only the new runner's isolated self-tests were executed.

## Interpretation and next experiment

A future receipt can demonstrate which local file bytes were tested and which subprocesses exited successfully. It cannot prove that GitHub Actions actually ran until the job log/run is independently read, and it cannot authenticate original label sources, timestamps, or custody. The `GITHUB_SHA` field is explicitly a CI-declared value, not an external attestation. A malicious party able to rewrite both code and CI logs can still misrepresent results.

Next: obtain a push-workflow run reader or a clean checkout; inspect job conclusions and compare logged SHA-256 inputs with the repository blobs. If that remains unavailable, pursue a separately retained, permission-differentiated witness design without claiming same-writer Git/Notion copies provide independence. No security settings or external credentials were changed.

## Reproduce

From `research/lumen`:

```sh
python -m unittest -q test_lumen373_receipt.py
python -O -m unittest -q test_lumen373_receipt.py
python lumen373_regression_receipt.py
```
