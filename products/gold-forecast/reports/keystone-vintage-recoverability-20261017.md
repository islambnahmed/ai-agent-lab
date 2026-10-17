# Keystone: prospective receipt recoverability audit (2026-10-17)

## Verified repository state
- `reports/prospective/` contains three receipts for origin 2026-10-11, issued 2026-10-12T17:12:52.272Z (h=1,7,30), sharing `historyHash=bcbfac86e29f02576a584cdab96be7915bce5d23f622f1e0c828964eda513f9f` and `historyLength=324`.
- `products/gold-forecast/.gitignore` excludes `/data/**`, which includes `data/vintages/`; that directory is not in `main`.
- `scripts/journal.mjs settle` unconditionally opens `data/vintages/<historyHash>.json` for each receipt and quarantines on missing file. Therefore a fresh checkout alone cannot settle these receipts.
- The README explicitly requires retaining the original private vintages. No snapshot backup in the authorized AI Agent Lab Memory folder was found during this cycle. This does not prove that the original issuing machine lacks the snapshots.
- `.github/workflows/gold-lab.yml` only runs tests on push/PR; it does not schedule issue/settle or preserve vintage artifacts.

## Impact and required recovery
- **No valid retrospective recovery from hash alone**: an SHA-256 digest cannot reconstruct the original 324-close vintage, and fetching a revised provider history is not a substitute.
- Recover the exact original `bcbfac86...513f9f.json` from the issuing machine or an authorized private backup; verify SHA-256 over `JSON.stringify(parsedRows)` and 324 rows before settlement.
- Back up future raw vintages privately inside authorized storage with source-license checks; keep public GitHub receipts only. Never treat a missing vintage as a verified result.
- A local read-only audit script and eight passing synthetic tests were produced in this cycle; code has not been integrated into CI. The earlier temporal-evidence gate is a separate pending patch.

## Caveat
This is a reproducibility/availability finding, not a claim that the three forecasts are incorrect. GitHub state was read on 2026-10-17; no live market outcome was verified.
