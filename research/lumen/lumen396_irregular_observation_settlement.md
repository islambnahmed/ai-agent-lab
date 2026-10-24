# Lumen 396 — Irregular observation-calendar settlement regression

**Date:** 2026-10-24. **Authorized repository:** `islambnahmed/ai-agent-lab`. **Code/test branch:** `sandbox/lumen-394-gold-utc`. **Report branch:** `sandbox/worker-c`. No main merge, external provider access, model promotion, or security changes.

## Question and scope

Lumen 395 verified h7/h30 synthetic **daily** calendars, leaving the explicit `calendar='observations'` contract untested. The important difference is that irregular data cannot promise a calendar target date in advance: horizons must count future *observed provider closes*, not calendar days. This cycle tested the real `issueReceipt` and `settleReceipt` implementations against gaps in a synthetic 260-row historical prefix.

## Verified artifact and checks

Added `products/gold-forecast/tests/journal-irregular.test.mjs` on the isolated branch. The synthetic series has a skipped calendar day every 17 observations (maximum gap two days). It tests **h1, h7 and h30**, with five cases each (15 cases total):

1. Receipt retains `calendar='observations'`, `targetDate=null`; maturity occurs at the exact h-th new observed close, with correct actual and model absolute error.
2. An incomplete future observation horizon stays pending, without an invented target date.
3. A present target observation is still pending on its own UTC day and matures only after that day closes. Before completion, target date remains unknown.
4. Equivalent UTC and negative-offset issuance/settlement instants preserve outcomes.
5. A changed historical-prefix price triggers vintage quarantine.

The initial test draft incorrectly expected the pending observation target date to be known before its day completed; this contradicted the documented irregular-calendar contract. Corrected that assertion in commit `956892d5f3d9eed9eeb568905ad2df544f593138`, preserving the more conservative behavior.

**Verified CI at final commit:** [Gold Lab MVP tests — 40131417207](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40131417207) and [AI Agent Lab CI — 40131417202](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40131417202) completed successfully. GitHub job steps confirm syntax checks, forecast regression tests, source parser regression tests, and lab validation all succeeded. The added cases are synthetic; CI success is not a live-price or independent-vintage evaluation.

**Test source:** [journal-irregular.test.mjs](https://github.com/islambnahmed/ai-agent-lab/blob/sandbox/lumen-394-gold-utc/products/gold-forecast/tests/journal-irregular.test.mjs)

## Decision and remaining evidence gap

No failure of the irregular observation-index settlement contract was reproduced by these cases; the current isolated patch now has synthetic regression coverage for h1/h7/h30 on both regular and irregular cadence. This **does not** establish that a provider's missing close is detectable: an omitted future row can shift the h-th *observed* close, and there is no authoritative calendar against which to detect the omission. It also does not prove a historical source was available at the receipt's issuance time; Git anchoring and independently archived vintages are still necessary.

Do not merge or promote a forecast model based on this cycle. Prefer independent archival and reconciliation of prospective receipts, provider availability and actual closes; pursue additional synthetic hardening only for concrete counterexamples.
