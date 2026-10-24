# Lumen 395 — Gold journal h7/h30 UTC settlement and provenance regression

**Date:** 2026-10-24. **Scope:** `islambnahmed/ai-agent-lab` only. **Test branch:** `sandbox/lumen-394-gold-utc`. **Report branch:** `sandbox/worker-c`. No merge to main, no live data, no security changes.

## Why this work

Lumen 394 demonstrated an end-to-end UTC calendar-day fix for a synthetic one-observation forecast. The untested assumption was that the same fix behaved consistently at horizons 7 and 30 and did not mask historical revisions or missing targets. Rather than further expanding a generic validator, this cycle tested the real `issueReceipt` and `settleReceipt` exports at both horizons.

## Reproducible change

Added `products/gold-forecast/tests/journal-horizons.test.mjs` on `sandbox/lumen-394-gold-utc` at commit `c647c0a6ac2ffb53424bccb599d5e5b98247db0c`. The fixture contains 260 synthetic calendar-day historical closes, an explicit synthetic source manifest, and exactly the future observations needed for each horizon. There are **10 new test cases** (five for each of h7 and h30):

1. Exact horizon target date and settlement equivalence between UTC and a -03:00 representation of the same instant; assert actual and absolute errors.
2. Target remains pending immediately before UTC midnight, then matures on the next UTC day.
3. A changed historical-prefix price is rejected as a revised vintage.
4. A missing target cannot be silently substituted with a later close.
5. Equivalent issuance instants retain the same target and matured actual.

**CI verified:** `Gold Lab MVP tests` run [40126899487](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40126899487) and `AI Agent Lab CI` run [40126899573](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40126899573) both completed with **success** at the test commit. The Gold job's syntax, forecast regression and source-parser regression steps all succeeded.

**Artifact:** [journal-horizons.test.mjs](https://github.com/islambnahmed/ai-agent-lab/blob/sandbox/lumen-394-gold-utc/products/gold-forecast/tests/journal-horizons.test.mjs)

## Conclusions and limits

The isolated Lumen 394 UTC patch now has passing end-to-end synthetic regressions for h1, h7 and h30, including provenance-prefix and target-date failure behavior for h7/h30. This does **not** prove source authenticity, independent historical vintages, forecast accuracy, or behavior for irregular observed-close calendars. CI success is limited to the tested branch; nothing was merged into `main`.

**Next evidence-first direction:** audit irregular `calendar='observations'` horizons for off-by-one and absent target-date cases; if no significant flaw emerges, prioritize independently archived real prospective receipts rather than repeatedly hardening synthetic tests.
