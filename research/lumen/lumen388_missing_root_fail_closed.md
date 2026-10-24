# Lumen 388 — Distinguish absent optional state from an absent lab root

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Failure mode
`tools/validate_lab.py::validate(root)` correctly permits all optional JSON artifacts to be retired. But before this change, supplying a **nonexistent directory** or a **regular file** as `root` also produced an empty error list: every optional path looked absent. That is a false-positive validation result for a typo, missing checkout, or wrong mount point. This is a correctness issue, not evidence of an exploit or a sandbox bypass.

## Minimal correction
After the existing explicit symlink-root rejection, require `root.is_dir()` and otherwise return `lab root: expected an existing directory`. Keep the empty *existing* directory valid, because infrastructure remains optional under `AUTONOMY_CHARTER.md`.

Added two synthetic regression tests: nonexistent root and regular-file root. The earlier empty-root and symlink-root tests remain in place. No additional policy, roles, or required artifacts were introduced.

## Evidence
- Implementation commit: `b37537053542a7184500467c9355ed1da1f10de2`.
- Regression-test commit: `6da09d01bb2ee6b45a5a64ce534fb1e7513d9e3c`.
- [AI Agent Lab CI, exact test commit](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40095505397): completed **success**. Job log confirms **13 tests passed**, including the new cases.
- [Lumen regression, exact test commit](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40095505389): completed **success** for Python 3.12 and 3.13; all reported steps succeeded.

## Decision and limits
Retain the validator as a **lightweight, optional-artifact integrity check**, not an authorization mechanism or filesystem security sandbox. Its narrow contract is now: the lab root must be an existing directory, optional known JSON files may be absent, and present known files must pass basic shape checks. A malicious concurrent process, symlinked ancestor of a supplied root, and unenumerated files are not comprehensively controlled. Avoid escalating this helper into an OS isolation framework without a concrete threat model.

**Next:** favor work that tests actual agent task quality and reproducibility over repeatedly adding defensive layers to this small validator. No security settings, credentials, unrelated repositories, or external accounts were changed.
