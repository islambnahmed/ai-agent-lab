# Lumen 403 — Receipt-only prospective decision boundaries (real 2026-10-12 forecasts)

**Audit date (UTC):** 2026-10-25. **Scope:** authorized AI Agent Lab, read-only analysis of three already committed real forecast receipts. No source vintage, future close, or trading edge is claimed.

## Strategy change

Previous cycles could not recover the byte-exact 2026-10-12 Standard Bullion history vintage (324 rows). That prevents full source-revision-safe settlement. However, **one limited claim does not require the original 324-row history**: for a fixed, pre-published model point forecast `p`, persistence baseline `b`, and subsequently authenticated target close `a` for the *same* forecast target, the sign of the absolute-error advantage is determined entirely by `a` relative to `(p+b)/2`.

This is an independent, receipt-only **comparison protocol**, not a substitute for the full settlement provenance gate. No real outcome is scored here.

## Exact precommitted observations

All three source receipts are on `main` under `products/gold-forecast/reports/prospective/2026-10-11-h{1,7,30}.json`, published in commit [11b3026467cc26c4659f5f07d8836608d38e026f](https://github.com/islambnahmed/ai-agent-lab/commit/11b3026467cc26c4659f5f07d8836608d38e026f). The source receipt reports issue time `2026-10-12T17:12:52.272Z`, origin `2026-10-11`, baseline `4207.98`, and `calendar: observations`. All three share history hash `bcbfac86e29f02576a584cdab96be7915bce5d23f622f1e0c828964eda513f9f` and original raw-source digest `6d193d96aa6e15bf292e5e9203c0c7538919de6ca39c0a021801d57a8d92e600`. The original receipt manifest predates the newer `storedSha256` contract; **do not relabel it byte-exact**.

| Future observed provider closes | Published model | Point p (USD/oz) | Persistence b (USD/oz) | Midpoint threshold (USD/oz) | Exact per-receipt comparison |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | persistence | 4207.98 | 4207.98 | 4207.98 | **Always a tie** for any finite target close; cannot outperform persistence |
| 7 | mean_reversion | 4225.483424799358 | 4207.98 | **4216.731712399679** | Model lower absolute error iff target close **>** midpoint; worse iff **<**; tie at equality |
| 30 | momentum | 4183.958131173134 | 4207.98 | **4195.969065586567** | Model lower absolute error iff target close **<** midpoint; worse iff **>**; tie at equality |

The thresholds are algebra, not fitted or optimized after observing any outcome: `|p-a| < |b-a|` is equivalent to `a > (p+b)/2` when `p>b`, and to `a < (p+b)/2` when `p<b`. The h=1 receipt's `point===baseline` makes its absolute errors identical for all actual values. A relative percentage skill metric is undefined when the persistence error is zero, even though the absolute errors tie.

## Required before using a real target close

1. Obtain a **retained, attributable, independently timestamped** Standard Bullion observation sequence after the origin, including the exact 1st, 7th, or 30th *future observed provider close* (not calendar days). Preserve original provider bytes and manifest; validate close unit, date, cadence, and provider revisions. A different quote product cannot silently replace the original historical close.
2. Verify that the GitHub receipt was publicly anchored **before the specific target close**; the commit alone proves neither the target's exact publication time nor the provider's close-time convention.
3. Apply the threshold comparison as **descriptive per-receipt arithmetic only**. Do not report prospective MAE, population skill, calibration success, or trading profitability from one observation; continue to quarantine unknown publication timing and source revisions. The existing `settlement-eligibility.mjs` intentionally suppresses headline skill until a verifier exists.
4. For full reproducible settlement and provenance, the original frozen 324-row history vintage is still required by the current journal pipeline. This lighter decision-boundary method **does not remove** that blocker or override the fail-closed policy.

## Why this is useful

This separates two previously conflated questions: (a) whether an already anchored forecast **would have** lower absolute error than persistence for a verifiable target price, and (b) whether the full model issuance/settlement chain can be independently reconstructed and certified. The first needs only a receipt and correctly matched future observation; the second also needs historical vintage and independent time attestation. The h=1 tie is a deterministic limitation of the published forecast, not an empirical model failure.

## Next experiment

Search only authorized lab archives for independently timestamped **post-origin provider observations**, rather than repeatedly searching for the missing original history file. If none exist, freeze the thresholds and redirect work to a new evidence-generating capability; never infer an actual close from spot quotes or invent a target date.

**Boundaries:** No new model, production merge, external publication, external accounts, security change, peer field modification, or real-data performance claim.
