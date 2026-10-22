# Khepri experiment 362 — receipt batch preflight and rollback

Date: 2026-10-22. Research-only branch; no production changes.

## Exact source and question
The main-branch `products/gold-forecast/scripts/journal.mjs` was fetched and copied byte-for-byte. Git blob SHA verified locally: `40671e74c7d6f215525c7c4301092583fc3b29dc`.

The `issue` command writes horizon 1, 7, and 30 receipts in a loop. A late validation failure can leave partial receipts. The real `forecast.mjs` requires at least 240 rows for horizon 30, versus 165 for horizon 1/7.

## Controlled source-level reproduction
Executed the **exact issuer script** in disposable local Git fixtures with synthetic daily history and explicit stubbed `issueReceipt` / `prepareProviderHistory` dependencies. The stub models the horizon threshold and permits fault injection; these are not real production forecast runs.

- Original: h30 failure after h1/h7 => **two receipts + one vintage remain**.
- Original: injected h7 failure => h1 receipt remains.
- Preflight-only patch prevents partial writes on validation errors, **but still fails** on injected I/O error at h7 (h1 remains).
- Preflight + rollback patch leaves no newly created receipts/vintages for either failure, publishes all three on success, preserves bytes on rerun, and preserves pre-existing vintages.
- `node --test atomic-preflight.test.mjs`: **10/10 passed**.
- `node --check`, `git apply --check`, and post-apply byte comparison passed.

## Proposed candidate
1. Compute every missing horizon receipt before any new file write.
2. Publish with exclusive `wx` opens and record only newly created paths.
3. On caught errors, remove newly created files in reverse order; report cleanup failures.
4. Print successful receipt messages only after completing the batch.

The candidate patch and test harness are in the local reproducible artifact accompanying this experiment. This branch report is evidence, **not** a deployed fix.

## Counterexamples and caveats
In-process rollback is **not** crash-consistent multi-file atomicity. Power loss, SIGKILL, concurrent readers/issuers, and rollback-delete failures remain. Existing receipts are skipped without verifying their semantics. No live provider data, real model forecast integration, or production issuance was tested. Prior experiment 358's issuer-script dirty-tree provenance issue remains independently unresolved.

## Reproduction
From the local artifact: `node --test atomic-preflight.test.mjs`.
