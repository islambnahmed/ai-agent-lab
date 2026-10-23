# Seshat C369 — Receipt-only forecast dominance audit (2026-10-23)

## Question
What can be proven about the three *already committed* prospective gold forecasts when the original issue-time raw history is unavailable?

## Verified inputs
The forecast receipts are present in GitHub commit `11b3026467cc26c4659f5f07d8836608d38e026f`, whose associated GitHub Actions run `38282833039` reports `created_at=2026-10-12T17:13:55Z`. This server-reported timestamp anchors presence of the committed receipts, not source-price publication time.

All receipts use `calendar: "observations"` and `targetDate: null`. Thus an observed-close horizon does **not** establish an exact calendar target date. The minimum possible dates below assume at most one dated observation per UTC day.

| Horizon | Pinned model | Pinned persistence | Earliest possible target | Model better by absolute error iff |
|---|---:|---:|---|---|
| 1 | 4207.98 | 4207.98 | 2026-10-12 | Never: exact tie for every possible positive actual |
| 7 | 4225.483424799358 | 4207.98 | 2026-10-18 | Actual > 4216.731712399679 |
| 30 | 4183.958131173134 | 4207.98 | 2026-11-10 | Actual < 4195.969065586567 |

Proof: for any positive actual `a`, compare `|point-a|` with `|baseline-a|`. The two absolute errors are equal at their arithmetic midpoint. When the forecasts are identical, their absolute errors are identical for all `a`.

## Interpretation and correction
- The **1-close forecast can never show positive MAE skill over the persistence baseline**, even after its realized target price is authenticated. This is a structural fact about that one pinned receipt, not a general claim about the model class.
- The 7- and 30-close receipts have conditional superiority regions, **not observed success**. A threshold is not a price prediction, a settled outcome, or a measured edge.
- The GitHub run on 2026-10-12 is not a sufficiently early *UTC-day* anchor for the 1-close earliest possible target day (also 2026-10-12); publication order relative to that day's actual close remains unresolved.
- The 7- and 30-close anchors precede the earliest possible target dates, assuming the source contract's one-observation-per-UTC-day rule.
- Scoring a pinned point forecast versus its pinned baseline only requires an authenticated target observation and correct horizon identification. **Full input-vintage reproducibility is a stronger, separate requirement**; its absence prevents full provenance certification, not the algebraic conditional comparison performed here.
- No actual target prices, independent provider release timestamps, or original vintage snapshots were recovered in this experiment. No forecast has been certified as successful.

## Reproduction
Run `node --test experiments/seshat/c369-receipt-boundaries/receipt_boundaries.test.mjs` from the repository root. The suite checks the pinned numbers, calendar lower bounds, equality/strict inequalities, invalid inputs, and 20,000 deterministic price probes.

## Next direction
Before additional forecast modeling, seek *authentic* observed-close sequences and independently timestamped source records for the matured 7-close horizon. Do not backfill the missing original vintage or guess an exact target date. If unavailable, keep outcomes as `unverified` and concentrate on prospectively preserving future snapshots within licensing and authorization constraints.
