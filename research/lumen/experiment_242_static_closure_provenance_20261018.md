# Lumen 242 — Static ESM closure / Git HEAD provenance audit

Date: 2026-10-18. Scope: authorized AI Agent Lab / `products/gold-forecast`.

## Verified source finding

The current issuance command in `products/gold-forecast/scripts/journal.mjs` checks six hard-coded files before recording `git rev-parse HEAD`, omitting the CLI itself. A later module added through a static import can also be omitted. This creates a **code provenance gap**, not evidence that a receipt was tampered with.

Current static module import closure, inspected from GitHub's default branch:

`scripts/journal.mjs` -> `journal.mjs`, `data.mjs`; `journal.mjs` -> `forecast.mjs`, `historical-integrity.mjs`, `data.mjs`; `forecast.mjs` -> `data.mjs`, `models.mjs`; `data.mjs` -> `historical-integrity.mjs`, `calendar_contract.mjs`. Node built-ins are excluded. A `package.json` change can also affect invocation.

## Experiment

Implemented a standalone local auditor using Node 22 `vm.SourceTextModule.dependencySpecifiers` (requires `--experimental-vm-modules`). It recursively walks local static imports, rejects dynamic imports / require / external packages / symlinks / out-of-root paths, and checks each runtime module and `package.json` byte-for-byte against **both Git HEAD and the index**, rather than trusting `git status`.

**14/14 local synthetic Git tests passed**. They include transitive dependency modification, staged changes, index-vs-worktree mismatch, `assume-unchanged` masking, untracked imports, symlinks, traversal, and dynamic imports. A comment containing `import(` causes conservative rejection; this is an explicit limitation.

## Limitations and next decision

Tests used isolated synthetic Git repositories, not a full checkout of the live Gold Lab. The connector permitted source reads, but the execution environment could not clone the repository (DNS unavailable). This tool is not integrated with the issuance command or CI. It does not prove source data authenticity, a remote timestamp, or that all runtime reads are accounted for.

Before any integration: run the standalone auditor against a real checkout, verify actual import closure, and decide whether its experimental VM flag and fail-closed false positives are acceptable. Do not claim production safety based on this local test.
