# C336 — Gold prospective snapshot integrity (2026-10-24)

## Decision
After C335 added CI coverage, investigate the integrity of the actual data used to issue and settle gold forecasts. Do not tune predictive performance on the inspected retrospective period.

## Reproducible failure found
`scripts/fetch_data.py` previously recorded SHA-256 of **raw HTTP bytes** in `fetch-manifest.json` but wrote a **re-serialized JSON payload** to `data/history.json`. The receipt issuance/settlement script loaded the saved file without verifying that it matched the manifest. Consequently, a locally edited, valid JSON history could be consumed under the original source metadata without detection. This is a provenance mismatch, not evidence of malicious activity.

## Change
1. Record `storedSha256` over the exact UTF-8 bytes saved to each successful `data/*.json` snapshot; keep `rawSha256` separately.
2. Before either `issue` or `settle`, require a successful history fetch, both 64-character hashes, expected provider URL, and an exact match between the saved file and `storedSha256`. Fail closed on mismatch.
3. Include the issuer, fetcher, new verification module, and package script mapping in the pre-issue Git dirty-file guard. This reduces the risk of claiming a pinned code commit while executing uncommitted issuance/provenance logic.
4. Add five Node and two Python offline regression tests, including tampered valid JSON, malformed JSON, missing hashes, failed fetch cleanup, wrong URL, and saved-byte parity.

## Verification
- Local Node: `node --test products/gold-forecast/tests/snapshot-integrity.test.mjs` — **5/5 passed**.
- Local Python: `python -m unittest discover -s products/gold-forecast/scripts -p 'test_*.py'` with only the new Python test file present in the isolated test tree — **2/2 passed**.
- `python -m py_compile .../scripts/fetch_data.py` — passed.
- `node --check .../scripts/journal.mjs` — passed.
- The five published source/test files were fetched from GitHub after upload and their Git blob SHA-1 values matched the exact files tested locally.
- **Not claimed:** full repository test pass, provider access, a live forecast, verified historical source authenticity, or demonstrated predictive skill. CI results must be checked separately.

## Operational consequence
Old locally cached `fetch-manifest.json` files lack `storedSha256`; prospective `issue` and `settle` now intentionally refuse them until `npm run data` refreshes the snapshot and manifest together. Original private vintages remain unchanged. Do not reissue existing receipt IDs; settlement still checks frozen vintages and exact targets.

## Remaining limitations
A digest binds two local files but cannot prove provider authenticity, independently establish fetch/issue time, or prevent an actor from rewriting both the data and manifest. Git timestamp anchoring of receipts still needs independent verification before prospective claims. No model selection, predictions, historical data, external accounts, or production branch were changed.
