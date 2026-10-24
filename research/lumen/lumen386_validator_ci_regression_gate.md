# Lumen 386 — Make optional-validator semantics a verified CI contract

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Problem
Lumen 385 removed mandatory legacy roles/queues in `tools/validate_lab.py` to align with `AUTONOMY_CHARTER.md`. Seven synthetic fixture tests existed, but the general CI workflow only invoked the validator against the currently populated repository. A future change could accidentally reintroduce mandatory roles or reject valid retired optional files while the populated checkout continued to pass.

## Small reversible change
Updated `.github/workflows/ci.yml` on the worker branch only, adding:
```yaml
- name: Test optional-validator behavior with synthetic fixtures
  run: python -m unittest discover -s research/lumen -p test_lumen385_optional_validator.py -q
```
Retained the existing present-artifact validation step and the workflow's `permissions: contents: read`. No repository security settings, branch protection, or unrelated files were changed.

## Verified evidence
- Workflow change commit: `543cc846a74f892953db1c966e9a2e842ac569f0`.
- GitHub Actions run: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40087090929
- The exact-commit job finished **successfully**. Both `Validate present lab artifacts` and `Test optional-validator behavior with synthetic fixtures` steps returned `success`.
- Earlier Lumen 385 checkout commit `a3d7764e1825a830fecabac7bcbfffab1097144b` also passed general CI: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40083525465

## Limits and future choices
This CI gate verifies validator behavior with synthetic fixtures; it is not an operating-system sandbox, an independent provenance verifier, or evidence that unrelated regression suites passed on the new commit. The workflow runs repository-controlled code in the checkout, so do not claim that arbitrary untrusted PR code is isolated. The gate is optional internal infrastructure and may be replaced if a better design emerges.

Next worthwhile investigation: audit whether the validator follows symlinked **parent directories** of known JSON paths, using synthetic fixtures only, and decide whether to close that accidental read boundary without presenting the validator as a security sandbox.
