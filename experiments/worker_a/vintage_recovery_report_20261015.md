# Worker A — Vintage recovery integration (2026-10-15)

## Problem
The prospective settlement command previously quarantined every receipt when
the ignored local `data/vintages/<historyHash>.json` snapshot was absent,
even when a fresh provider response still contained the exact original series.
A receipt hash alone does **not** prove its issue time or the source's truth.

## Change
In branch `sandbox/worker-a-vintage-recovery-20261015`:
- Added `products/gold-forecast/vintage-reconcile.mjs`.
- Updated `products/gold-forecast/scripts/journal.mjs` to attempt exact
  original-prefix recovery **only** when the local vintage file is missing.
- If the local vintage exists, verify its exact hash and check all overlapping
  provider closes for revisions before appending new observations.
- Missing original prefix, changed historical prices, missing origin, corrupt
  local vintage, or malformed metadata fail closed.

## Evidence
- Local Node 22 test suite: **10/10 passed**, including exact-prefix recovery,
  rolling-window overlap, historical revision, lost prefix, and corrupted cache.
- GitHub Actions on commit `0efc6293ff0d44fb1d1339fe3073c5d0a257278e`:
  workflow runs `38760558014` and `38760557988` both **success**.
- A dedicated regression test file was tested locally but was **not published**
  because the GitHub write was blocked by platform safety checks. The successful
  existing CI therefore does not imply the new edge-case tests ran in CI.
- Changes remain on an isolated branch, not `main`.

## Limits and next evidence
This does not restore a rolled-away or revised historical vintage. If the
original 324-row prefix is no longer reproducible, the receipt must remain
quarantined until an independently preserved original snapshot is available.
No new live provider dataset was retrieved in this cycle; no prospective gold
forecast was settled or shown to outperform persistence.

## Reproduction
`node --test products/gold-forecast/tests/vintage-reconcile.test.mjs`
can run after adding the local test file to a working copy; it is not present
in the published branch. Production `npm run settle` still requires a fresh
provider snapshot and manifest.
