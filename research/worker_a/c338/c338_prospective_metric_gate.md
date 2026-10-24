# C338 — Gold Lab: fail-closed prospective performance reporting (2026-10-24)

## Verified defect
The existing `scripts/journal.mjs` directly aggregates every `settleReceipt(...).status === 'matured'` outcome into headline MAE. `settleReceipt` verifies the price-vintage prefix and that a later observed target price exists, **but does not verify that the receipt was publicly anchored before the target close**. Thus a receipt could be retrospectively published and still be counted as a prospective prediction. The C337 publication audit found the three current receipts have `calendar=observations` and `targetDate=null`, so their prospective timing remains unproven.

## Change
- Add `settlement-eligibility.mjs` with `gateSettlement` and `summarizeSettlements`.
- The CLI now downgrades arithmetic `matured` outcomes to `provisional`, preserving their errors for investigation but excluding them from headline prospective MAE.
- Report each horizon's provisional, pending, quarantined and verified-matured counts separately. The current verified-matured count is **always zero** because no independently authenticated close-time verifier exists yet.
- The issuance dirty-code guard now includes the reporting policy and script, preventing silent uncommitted changes to the reporting code during issuance.
- Keep existing receipts unchanged; do not fabricate target timestamps or promote date-only anchors to market-close proof.

## Evidence
- 10/10 offline Node tests passed locally; JS syntax checks passed for module and CLI.
- A static integration assertion confirmed the CLI calls the gate before summarizing.
- No live settlement executed; no claims of forecast skill, measured model performance, or provider close-time authenticity.

## Policy limitation / next step
The policy intentionally sacrifices headline metrics until a separate independently verifiable publication + provider-close evidence path exists. Future code must not simply trust an editable `verified=true` field or a self-declared target close. The C337 publication anchor by itself is insufficient for the `targetDate=null` receipts. PR #10's snapshot integrity fix and PR #11's anchor audit are separate, unmerged changes; this patch is independently reviewable and must be reconciled with both before any merge.
