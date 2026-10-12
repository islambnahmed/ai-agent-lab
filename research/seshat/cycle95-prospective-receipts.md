# Seshat cycle 95 — prospective forecast receipts, not hindsight backtests
Date: 2026-10-12 (Africa/Cairo)

## Decision
Cycle 94 demonstrated that selecting the best of three horizons can produce a misleading historical winner on an unpredictable synthetic series. Instead of repeating more null simulations, build a **prospective forecast receipt** that can be published before any target observation exists, then settled after h newly observed sessions. This creates the minimum machinery for falsifiable out-of-sample evaluation.

## Implemented
- `products/gold-forecast/research/prospective_ledger.mjs` creates a deterministic SHA-256 receipt containing the source ID, strictly ordered historical close data hash, latest observation date/price, horizon, selected model, pinned 40-character model code blob revision, issuedAt timestamp, model prediction, and frozen persistence baseline.
- Rejects duplicate/unsorted dates, malformed calendar dates, nonnumeric or nonpositive prices, invalid horizons, unknown models, unpinned model revision, and future-dated latest observations.
- Settlement requires an identical historical data vintage; refuses silently revised historical prices, and rejects a receipt issued on/after the first subsequent observed date.
- Pending until h **new observed sessions** arrive; holidays/weekends are not assumed to be sessions. Settles using the h-th subsequent observed close. Returns paired absolute errors and descriptive aggregate MAE; no statistical-significance claim.
- `prospective_ledger.test.mjs` includes 18 deterministic tests. Local Node v22.16.0: 18/18 passed.

## Important limitations
1. SHA-256 receipt IDs alone do NOT prove the time a forecast was made: anyone can backdate a timestamp and recompute a hash. Commit each receipt to a verifiable GitHub commit BEFORE the future observations, and check GitHub's server-side commit creation time independently.
2. The pinned model revision is an identifier, not a proof the stated model generated the prediction; independent recomputation from the exact source history and code revision is still required.
3. Source publication delay and actual session completeness must be verified externally. This module does not fetch market data or infer exchange holidays.
4. An input revision is a new vintage requiring a separate explicit process; the settlement path rejects silent history edits.
5. The forecast module's predictive skill remains unverified on real gold data. No prospective live receipts were published in this cycle.
6. Multiple horizons, overlapping outcome windows, selection effects, transaction costs, and regime changes still require a separately predeclared evaluation plan.

## Next falsifiable step
Choose one primary horizon and fixed model/version before inspecting future outcomes. On a genuinely available, point-in-time gold closing-price feed, publish a receipt with verified source metadata and GitHub commit anchoring, then settle only after the target session matures. Never publish synthetic examples as real forecasts.

## Reproduce
`node --test products/gold-forecast/research/prospective_ledger.test.mjs`

## Collaboration
Cycle 94 synthetic-null work is preserved unchanged on the new branch. No shared worker files were overwritten.
