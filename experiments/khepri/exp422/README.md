# Khepri experiment 422 — SQLite revision-history mutation audit

Date: 2026-10-24. Scope: authorized AI Agent Lab only. Research prototype; no production or remote resource mutations.

## New evidence and correction to exp421

The trigger pattern used by exp421 does **not** prevent all accidental direct-SQL revision resets. Two reproducible counterexamples:

1. With `PRAGMA recursive_triggers=OFF`, `INSERT OR REPLACE` on an existing `heads.path` implicitly removes and reinserts a row **without firing the BEFORE DELETE trigger**. A new content value can retain revision 1, causing a receipt issued against revision 1 to pass and overwrite the intervening content.
2. `UPDATE heads SET path='new'` moves a primary key without touching the old trigger's guarded columns. Recreating the original path at revision 1 similarly makes a stale receipt appear current.

These are tests of a faithful **schema replica** of exp421, not a claim of executing its original source byte-for-byte. The original source was inspected before building the test. Run the committed, standard-library-only `regression_probe.py` to reproduce five assertions:

```bash
cd experiments/khepri/exp422
python -m unittest -q regression_probe.py
```

## Defensive experiment

A separate local, downloadable extended prototype adds: `seen_paths` history, a BEFORE INSERT reinsert guard, immutable path names, UPDATE-first writes, first-upgrade revocation of outstanding synthetic approvals, and migration regression tests. It also confirms an important compatibility cost: a BEFORE INSERT trigger fires even on the conflict-update branch of an `INSERT ... ON CONFLICT DO UPDATE` statement. Therefore, simply installing the new trigger breaks the original UPSERT helper. UPDATE-first is necessary for this prototype.

**Local verification:** 22/22 extended unit tests passed, including two independent OS processes. A deterministic benchmark covered 480 constructed cases (SEO- and gold-labeled paths). In 240 deliberately history-resetting cases, the previous schema accepted a stale approval; the hardened prototype rejected the direct SQL. Other 240 cases verified clean writes, unrelated-path writes, and legitimate stale rejection. These are deliberately constructed tests, **not** attack-prevalence estimates.

## Limits and required migration care

- Do not deploy this research code as an authorization service. Receipt IDs are synthetic labels, not authentication.
- SQLite schema/file administrators can bypass trigger-only protections. The `seen_paths` ledger is not tamper-proof.
- Upgrades must quiesce writers; the research migration is not an atomic DDL/backfill/revocation rollout.
- Previously reset history cannot be reconstructed; invalidate/re-evaluate old approvals before resuming writes.
- Results do not establish GitHub, Notion, Drive, distributed, or LLM security.

**Lesson:** invariants need tests across the full SQL mutation grammar, including REPLACE, primary-key UPDATE, UPSERT, and migration behavior. A defensive trigger can also break valid writes; verify compatibility before rollout.

**Local full reproducibility bundle:** `khepri_exp422_reproducible.zip` (contains `approval_guard.py`, 22-test suite, `benchmark.py`, `results.json`, and detailed README). The compact committed regression probe is independently runnable.
