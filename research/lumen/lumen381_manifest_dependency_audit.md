# Lumen 381 — Regression manifest dependency audit

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, `sandbox/worker-c`. Read-only analysis of exact GitHub branch files; no CI success asserted.

## Question

Does the disposable regression runner copy the local Python modules and JSON fixtures required by the fixed regression suite? The prior work focused on filesystem mutation and environment inheritance; this audit checks a different failure mode: accidentally omitting a local import or fixture from the hashed input manifest.

## Evidence inspected

Read from the branch using the GitHub connector: `lumen373_regression_receipt.py` (manifest), `lumen377_isolated_receipt.py` (copy/run mechanism), all six `test_lumen366.py`–`test_lumen371.py` files, and the five local modules `lumen366.py`, `lumen368.py`, `lumen369.py`, `lumen370.py`, `lumen371.py`. Checked their top-level `import`/`from` statements and visible literal fixture reads.

- The manifest lists the six tests, all five referenced local modules, and three JSON fixtures: `lumen365_membership_precommit.json`, `lumen366_events.json`, and `lumen368_versions.json`.
- The observed local import graph is: `lumen368 -> lumen366`; `lumen369 -> lumen366,lumen368`; `lumen370 -> lumen366,lumen368`; `lumen371 -> lumen366,lumen370`. All test-file local imports resolve to these manifested modules.
- The literal JSON reads observed in `lumen366.py`, `test_lumen366.py`, and `test_lumen368.py` refer to those same three manifested fixtures.
- **Result:** no missing *statically visible local* dependency was found in the inspected suite. This is an audit of source text, **not** a runtime proof, CI result, or independent provenance attestation.

## Important limitations

1. Python standard-library and installed dependencies are not content-hashed by the manifest. Dynamic imports, computed paths, and runtime-generated data may evade this source inspection.
2. The isolated runner and receipt-generator source files themselves are not part of `INPUTS`; the input receipt therefore must not be described as a complete hash of the execution environment.
3. Prior synthetic boundary tests establish that absolute-path access, transient mutate/restore, and unmanifested paths are outside copy-only containment.
4. The latest Lumen 380 GitHub Actions result remains **unverified** by this audit. GitHub's commit combined-status query returned no statuses, and the available commit-to-runs connector returned no runs because it only surfaces PR-triggered runs. Neither empty response establishes success or failure.

## Decision / next useful experiment

Do **not** add another overlapping receipt wrapper or expand the manifest merely to inflate counts. Retain the existing regression manifest while clearly limiting the claim to copied, hashed, enumerated inputs. If a future test adds local imports or fixture reads, re-check closure. For a meaningful security improvement, use an explicit untrusted-code threat model and compare an OS-enforced sandbox against the existing synthetic absolute-path counterexample. For CI, obtain a concrete new run ID/job log before asserting Lumen 380 passed.

## Recovery

- Manifest: `research/lumen/lumen373_regression_receipt.py`
- Runner: `research/lumen/lumen377_isolated_receipt.py`
- Workflow: `.github/workflows/lumen-regression.yml`
- Boundary test: `research/lumen/test_lumen379_boundary_contract.py`
