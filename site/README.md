# Gold forecast website MVP — Keystone, 2026-10-09

This is a static Arabic RTL website shell. It uses no external scripts and publishes no invented prices.

Preview: from the repository root, run `python -m http.server 8000`, then open `/site/`.

The `site/forecast.json` manifest intentionally says `unavailable`. The client will show a number only for a valid `publishable` manifest with a positive finite USD-per-troy-ounce forecast, model ID, HTTPS source, target date, generation time, information cutoff, and expiry. Invalid, missing, future-dated, and stale manifests fail closed.

IMPORTANT: Browser-side schema checks are NOT independent verification of price sources or publication timestamps. Only a separately audited data pipeline should ever mark a forecast publishable. This prototype is not a live feed or investment advice.

Local development tests: 11 Node.js tests passed in the Keystone cycle-30 workspace on 2026-10-09. The test file could not be uploaded to GitHub because the connector blocked that write; this claim does not imply tests ran in CI.

Next: connect an independently verified and versioned forecast feed, add provenance/point-in-time checks on the publishing side, and wire tests into CI.

## Cycle 31 correction (2026-10-09)

The original validator could display a forecast whose target date had already passed if its expiry was set far into the future. The client now rejects a completed UTC target day regardless of expiry. The target is a calendar day rather than a midnight instant, so same-day forecasts can still pass before the day ends.

Locally, 16 Node.js checks passed with `node --test tests/test_gold_site.mjs` using the cycle-30 test bundle plus five new regression cases. **The test file was not committed**: GitHub rejected two attempts to create it. The branch therefore contains the application fix but does not yet have committed regression tests. Do not interpret local results as CI evidence.

No live or independently verified gold forecast has been published. The placeholder remains unavailable.
