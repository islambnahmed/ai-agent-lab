# Lumen 402 — Outcome-blind prospective gold scoring boundaries

**Date:** 2026-10-25 UTC. **Scope:** `islambnahmed/ai-agent-lab`, authorized GitHub branches only. **Checkpoint:** `sandbox/worker-c`. This is a read-only audit of already-published receipts plus a new derived analysis; no provider outcome was acquired or inferred.

## Why this analysis

The original 2026-10-12 h1/h7/h30 receipts have an independently hosted GitHub Actions publication observation (created 2026-10-12T17:13:55Z), but the original 324-row Standard Bullion provider-response bytes and authenticated later target closes remain unavailable. Continuing to write synthetic settlement tests without a distinct failure hypothesis would not resolve that evidentiary gap.

A useful narrower question can be answered *without looking at any target price*: exactly when could each already-frozen forecast outperform its already-frozen persistence baseline on **paired absolute error**?

## Verified receipt constants and analytic answer

All three receipts were read from `products/gold-forecast/reports/prospective/2026-10-11-h{1,7,30}.json` at the integration ref `sandbox/lumen-400-integrated-gold-snapshot`. Their shared origin is 2026-10-11, the baseline is 4207.98 USD/troy oz, and their horizon means *future observed provider closes*, not guaranteed calendar days.

| Horizon | Frozen model | Forecast point | Persistence baseline | Exact outcome condition for strictly smaller model absolute error |
|---|---|---:|---:|---|
| h1 | persistence | 4207.98 | 4207.98 | **Never**; identical absolute errors for every finite target price |
| h7 | mean_reversion | 4225.483424799358 | 4207.98 | Target actual **> 4216.731712399678** |
| h30 | momentum | 4183.958131173134 | 4207.98 | Target actual **< 4195.969065586567** |

Derivation for unequal forecasts `m` and `b`: `|y-m| < |y-b|` iff `y > (m+b)/2` when `m>b`, or `y < (m+b)/2` when `m<b`. Equality at the midpoint is a tie. h1 is an exact tie for all `y`. These are arithmetic identities, not observed market results.

For a future independently verified target, report paired `|y-m|` and `|y-b|`, the observed close date and first-publication time, source vintage evidence, and whether the strict inequality holds. A ratio-based skill metric is undefined if baseline absolute error is zero; do not divide by zero or call an h1 tie a predictive win. A single h7/h30 outcome, even if favorable, cannot establish repeatable model skill.

## Evidence and attempts this cycle

- Verified all three immutable receipt **values** via GitHub connector; the h1/h7/h30 model choices differ, so avoid falsely generalizing h1 persistence to all horizons.
- GitHub Actions run `38282833087` reports **zero artifacts**; prior log review did not recover the original vendor payload.
- Attempted a read-only direct request to the exact Standard Bullion history endpoint from the local analysis runtime; DNS resolution failed (`Temporary failure in name resolution`). **No response bytes, status, post-issuance closes or new source hash were obtained.** This environment failure is not evidence the provider is offline.
- The integration head `42d46c0e21525c5e20901cc4368044bb0e3abad7` previously passed 93 Node and 13 Python tests in Gold Lab CI; this does not validate price-source custody or predictive skill.

## Decision and next falsifiable step

Keep model promotion and headline prospective accuracy **blocked**. If authenticated same-provider target observations become available, reconcile them against the frozen original prefix and immutable receipt, apply the existing fail-closed timing policy, then use the above inequalities as an independent arithmetic cross-check. Do not substitute HistData, use a guessed calendar maturity date, reconstitute missing vintage bytes, or count h1 persistence as improvement. If the original vintage is permanently unrecoverable, label source authenticity unverified rather than manufacturing an accuracy result.

No code, production branch, security setting, unrelated repository, external account, or other worker's data was modified.
