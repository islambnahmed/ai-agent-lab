# Keystone: Gold Lab UI source-of-truth race audit (2026-10-11)

## Scope
Independent review of `products/gold-forecast/app.mjs` on `feature/gold-forecast-mvp-20261008` (read-only). Source reviewed on 2026-10-11. This note does not imply deployment.

## Verified defects
1. `refresh()` awaits both historical and spot requests; if the user selects DEMO or uploads CSV before they finish, the late refresh can overwrite the user's choice, prices and status.
2. CSV import preflights `forecast(series,30)` even when the chosen horizon is 1 or 7, so a valid shorter-horizon import can be rejected.
3. `spotData()` accepts finite but non-positive and crossed dealer quotes (ask < bid). If a fulfilled spot payload is invalid, the previous ask/bid remain on screen.

## Minimal proposed repair
- Extend state with a monotonic `epoch`. At refresh start, capture `const epoch=++state.epoch`. After `Promise.allSettled`, return without updating any UI if `epoch!==state.epoch` (release loading/disabled state first).
- Increment `state.epoch` at the start of `demo()` and immediately upon selecting a CSV file, before awaiting `file.text()`. After the await, ignore that CSV if its captured epoch is stale.
- Replace `forecast(series,30)` in the CSV preflight with `forecast(series,state.horizon)`.
- Reject `ask<=0`, `bid<=0`, or `ask<bid`, as well as non-finite quotes. Clear both displayed quote fields if quote parsing fails.

## Test evidence
A locally evaluated patched version of the real `app.mjs` text passed **four isolated JavaScript mock-DOM scenarios**:
1. Pending live request resolves after DEMO; DEMO remains selected and displayed.
2. Pending live request resolves after a 170-row CSV import at horizon 7; CSV remains selected; mock forecast rejects horizon 30 to catch the original preflight bug.
3. A delayed CSV file read resolves after DEMO; the late CSV cannot replace DEMO.
4. Negative, zero and crossed quotes are rejected.

The harness mocked DOM, fetch, forecast and normalization. These checks do **not** establish real-browser correctness or CI status. The patch itself was **not committed**: GitHub `update_file` rejected the write with a safety check. No attempt was made to bypass that restriction.

## Next useful verification
Add reproducible Node mock-DOM tests to the PR branch once permitted, run the existing scoped CI, then manually verify live CORS/API shape, data freshness and attribution before merging. Do not claim the site is production-ready.
