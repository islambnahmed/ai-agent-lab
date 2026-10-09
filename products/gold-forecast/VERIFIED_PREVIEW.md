# Lumen: fail-closed gold feed preview (2026-10-09)

## What changed
- Added `source_quality.mjs` for strict timestamp, units, ordering, and freshness checks.
- Added `feed_gate.mjs` to classify each refresh as live, history-only, spot-only, or unavailable.
- Added `app_verified.mjs` and `verified.html` as a reversible preview. The original `index.html` and `app.mjs` remain untouched.
- Preview clears the old quote, forecast, chart, and audit **before** requesting new data. A failed refresh cannot keep the previous price under a live badge.
- Added deterministic feed-classification tests and a simulated browser DOM test covering success followed by total outage.

## Run
From the repository root: `python -m http.server 8000 --directory products/gold-forecast`
Open `http://localhost:8000/verified.html`.
Run tests: `node --test products/gold-forecast/tests/*.test.mjs`.

## Release gates
This is **not deployed** and is **not a live-browser acceptance test**. Verify the provider's current JSON schema, real browser CORS, historical data semantics, quote age during market closures, and licensing/attribution before replacing the main page. The 15-minute quote and seven-day history age limits are heuristics, not vendor promises. Synthetic test prices are not evidence of forecast accuracy.

Do not call the preview production-ready until a real-browser test and independent price cross-check pass.
