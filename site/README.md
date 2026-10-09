# Gold forecast website MVP — Keystone, 2026-10-09

This is a static Arabic RTL website shell. It uses no external scripts and publishes no invented prices.

Preview: from the repository root, run `python -m http.server 8000`, then open `/site/`.

The `site/forecast.json` manifest intentionally says `unavailable`. The client will show a number only for a valid `publishable` manifest with a positive finite USD-per-troy-ounce forecast, model ID, HTTPS source, target date, generation time, information cutoff, and expiry. Invalid, missing, future-dated, and stale manifests fail closed.

IMPORTANT: Browser-side schema checks are NOT independent verification of price sources or publication timestamps. Only a separately audited data pipeline should ever mark a forecast publishable. This prototype is not a live feed or investment advice.

Local development tests: 11 Node.js tests passed in the Keystone cycle-30 workspace on 2026-10-09. The test file could not be uploaded to GitHub because the connector blocked that write; this claim does not imply tests ran in CI.

Next: connect an independently verified and versioned forecast feed, add provenance/point-in-time checks on the publishing side, and wire tests into CI.
