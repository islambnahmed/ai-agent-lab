# Seshat C374 — conservative forward-only issuance

Date: 2026-10-24. After C370–C373's retrospective revisions and all-phase sensitivity audit, move to **new prospective issuance** with a falsifiable UTC date-order gate. This protocol is committed before the live fetch.

## Precommitted protocol
1. On a fresh GitHub Actions run, read Standard Bullion's public rolling one-year XAU/USD series; use unchanged production parser and issueReceipt implementation. Do not publish raw provider payload.
2. Under the explicit assumption **at most one observation per UTC calendar date**, the earliest possible h-th later close is origin UTC date + h calendar days. Only issue if this earliest date is strictly AFTER the UTC issuance date. Reject all other horizons, including a potentially already-matured H1 on a lagged feed.
3. Issue all and only eligible horizons among H1, H7, H30. Record forecast receipt, model/code SHA, normalized-series history hash, raw response SHA-256, retrieval time, CI run ID, and eligibility decisions. The first successful run for each originDate/horizon is canonical; no selecting favorable later re-runs.
4. GitHub Actions has read-only contents permissions. Logs and a 30-day artifact preserve **derived receipts only**, not licensed vendor raw history. No main-branch changes.
5. Outcome: the h-th strictly later observed close, not an assumed calendar-day price. Do not replace a source/definition mid-test. If original vintage/prefix or same-definition evidence is unverifiable, mark provisional/quarantined, not certified. Compare with origin-price persistence by paired absolute error; no claim of skill from a single result.

## Why this differs from C373
C373 examined retrospective phase instability. C374 precommits a new forward-only gate and issues code-pinned receipts before a future eligible target, with GitHub Actions as an external script-execution timestamp. This does NOT authenticate the vendor or guarantee provider historical data custody.

## Commands
Offline: node --test experiments/seshat/c374-forward-issuance/eligibility.test.mjs

CI live: node experiments/seshat/c374-forward-issuance/issue_forward.mjs

Do not rerun to choose a favorable prediction. Any subsequent observations are evaluated against the first valid receipt.
