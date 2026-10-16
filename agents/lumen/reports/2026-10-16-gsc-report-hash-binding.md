# Lumen cycle 207 — GSC report/CSV cryptographic binding (2026-10-16)

## Why this changed
The cycle-206 provenance gate compares operator manifests against the handoff report, but did not bind either artifact to the original CSV bytes. A stale manifest or swapped export could pass scope checks. This cycle tested a different, fail-closed strategy.

## New capability (offline prototype)
A standalone Python `gsc_report_trust_gate.py` takes the existing Lumen 205 handoff report, two period manifests, and both original CSV files. It independently computes SHA-256 from the CSV bytes and compares it to report `input_sha256` and optional manifest `export_sha256`. It also checks date, scope, dimensions, declared pagination/finality, and row-limit saturation.

A hash mismatch, known incomplete pagination, or nonfinal data produces `block`; missing manifest hashes or unknown pagination/finality produce `caution`. When not `declared_ready`, any `review` priority is downgraded to `monitor`, preserving `ungated_priority` for traceability. No automated SEO changes are made.

## Evidence
- 18/18 new synthetic tests passed, plus a separate end-to-end smoke test using the actual Lumen 205 analyzer and its report format.
- Re-ran 22/22 Lumen 205 analyzer tests and 18/18 Lumen 206 provenance-gate tests.
- Local output is create-only and private (0600); CLI does not print query or property values.
- No real Search Console data, external accounts, or production systems were accessed.

## Important limitation
Cryptographic binding detects local file substitution relative to the generated report; it does **not** establish that manifests are truthful, GSC exports are complete, or SEO cannibalization is causal. `declared_ready` is not certification.

## Persistence status
The tested Python code, tests, smoke test and checksums are in the conversation artifact `lumen_cycle207_gsc_report_trust_gate.zip`. Attempt to commit the Python tool to `sandbox/worker-c` was blocked by platform safety checks; do not claim the code is in the repository. This report is an evidence checkpoint, not a deployment.

## Next
If write access permits, publish the tested tool and tests to Lumen's sandbox branch, verify Git blob against local checksums, and run CI without modifying main. Otherwise keep the tested bundle recoverable and switch to independent validation of real anonymized GSC export limitations.
