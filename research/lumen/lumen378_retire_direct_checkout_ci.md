# Lumen 378 — Retire redundant direct-checkout CI execution

**Date:** 2026-10-24 (Africa/Cairo). **Authorized scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Decision and evidence

Lumen 377's isolated runner was previously described as locally tested but not CI-verified. That uncertainty is now resolved: GitHub Actions run [40051924397](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40051924397) completed successfully on commit `aa35865ba893d2e4468874766f8acb99f6808e32`. The two jobs (Python 3.12 and 3.13) each reported 7 regression-receipt self-tests, 6 isolated-runner self-tests, and **79 regression tests in each of normal and optimized modes** for *both* the old direct-checkout runner and the isolated runner. Isolated receipts reported `all_passed: true`, no source drift, and no snapshot drift.

Running the same 79-test suite directly against the checkout after the isolated runner was validated provides little additional coverage, while permitting an accidental test write to alter the checkout before the drift detector notices it. The older direct-runner implementation remains in the repository and its seven self-tests remain in CI; only its redundant execution step was removed from `.github/workflows/lumen-regression.yml`. The isolated runner now performs the full suite.

## Verification of the change

Workflow change commit: `68033a55940948607160697519b7342a3eae0532`.

[GitHub Actions run 40056041287](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40056041287) completed **successfully** on that exact commit. The 3.12 and 3.13 job logs independently show:

- 7/7 regression-receipt self-tests passed in each Python version.
- 6/6 isolated-runner self-tests passed in each Python version.
- 79/79 full regression tests passed in each of the normal and optimized modes for each version (316 full regression test executions).
- Both isolated receipts: `all_passed: true`, `snapshot_drift: []`, `source_drift: []`, and subprocess exit codes 0.
- The workflow job list no longer includes the direct-checkout regression execution step.

The removed duplicate had previously executed another 316 regression tests. This is a reduction in redundant executions, **not** a reduction in the distinct suite or Python/mode matrix.

## Tradeoffs and boundaries

The direct runner is retained for manual diagnostics and comparison; its removal from the automatic workflow sacrifices an independent execution-path cross-check. This is reversible with a one-step workflow restoration if isolated behavior becomes suspect. Temporary copied inputs are not an OS sandbox: tests can still use absolute paths, unmanifested imports or deliberate permission changes. The hashes are local observations, not independently witnessed source provenance or immutable custody. CI passing does not prove that data sources are trustworthy.

## Next useful direction

Stop adding overlapping receipt wrappers. Prioritize an evidence-based threat model for the actual trust boundary, and either introduce a genuinely enforced read-only mount/OS sandbox in CI or explicitly limit the claim to accidental relative-path mutation protection. Benchmark changes against concrete escape attempts rather than more success counters.
