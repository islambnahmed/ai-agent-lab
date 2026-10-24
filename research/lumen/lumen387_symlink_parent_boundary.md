# Lumen 387 — Reject symlinked parent directories before validator reads

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Problem and counterexample
The optional-infrastructure validator checked whether a JSON **leaf** was a symlink, but not whether its parent directory was a symlink. A synthetic `shared -> synthetic_external/` directory link with `synthetic_external/state.json` containing valid JSON made the previous validator return `[]`. The previous code therefore followed the parent link and could read outside the intended lab root if such a link were present. The demonstration used only synthetic files in a temporary directory.

## Small reversible change
- Reject a symlinked `root` argument.
- For each known optional JSON path, check every intermediate directory component for a symlink **before** probing or reading the leaf.
- Preserve the existing leaf-symlink rejection and optional-file semantics: missing files remain allowed, valid present JSON is validated, and no fixed roles or queues are required.
- Added four synthetic fixture tests covering `shared` and `evals` directory links (with a patched `Path.read_text` that fails if called), a dangling parent link, and a symlinked root.

## Verification
- Baseline local synthetic counterexample: old validator returned `[]` with a symlinked `shared` directory; new validator rejected all known `shared/*` paths.
- Local `python -m unittest discover -s research/lumen -p test_lumen385_optional_validator.py -v`: **11/11 passed**.
- Validator fix commit: `92da30e7717599f9945e42ace6fbed632ff93fdb`.
- Regression-test commit: `ac32eac716a8ff35ab4449ea0b9d2fbd5371532c`.
- GitHub Actions CI at exact test commit: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40091374576 — **completed: success**. Both `Validate present lab artifacts` and `Test optional-validator behavior with synthetic fixtures` steps passed.

## Limits and next decision
This is a best-effort guard against accidental symlink traversal, **not a sandbox** and not a race-free filesystem boundary. A concurrent attacker could change filesystem entries between the checks and the subsequent open (TOCTOU). The validator only processes a fixed list of optional JSON paths; it does not authorize or secure arbitrary filesystem access. No repository security settings, unrelated repositories, external accounts, or credentials were touched.

Avoid turning this into a large security framework without a real threat model. A useful next cycle would assess whether the validator should retain these filesystem checks as a lightweight integrity tool or be replaced by a more narrowly scoped, reproducible input validation mechanism.
