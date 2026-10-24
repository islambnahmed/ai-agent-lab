# Lumen 391 — Gold prospective maturity: reject future-dated evidence

**Date:** 2026-10-24 (UTC verification). **Scope:** `islambnahmed/ai-agent-lab`, worker branch `sandbox/worker-c`. **Decision:** No model promotion or performance claim.

## New counterexample and fix

The preexisting `research/lumen/cycle342_prospective_claim_gate.py` validated the relative order of issue, anchor and target-publication timestamps, but **did not compare any of them to the current UTC time**. Consequently a synthetic claim with a publication timestamp in 2099 and all four supplied verification flags set to boolean `true` could be classified `eligible_for_scoring`, even though its supposed outcome cannot have been published yet.

The corrected `screen` captures the UTC current time once per call and:
- returns `invalid_receipt` for a future `issuedAt`;
- returns `insufficient_evidence` for future `anchorObservedAt` or `targetFirstAvailableAt`;
- preserves existing date-order, source, price and flag checks.

Four new synthetic regression test methods cover future issuance, future external anchor, future target publication, and an unmatured 30-observation claim. They use dates in 2099 to avoid brittle dependence on the exact execution day. **This is structural screening, not independent verification of timestamps or source vintages.** The self-supplied `true` flags remain untrusted without external checks.

Code commit: `866f4d5944a56765eb6150c4b643ee5bf6ab4e77`. Test commit: `f8958f2ca54fc84ed54f033fa8f30d0c045c9082`.

## Independently rechecked repository evidence

Read the three `main` receipts for origin `2026-10-11`, and separately read their blobs at the original anchoring commit `11b3026467cc26c4659f5f07d8836608d38e026f`. The blobs match byte-for-byte at both refs:

| Horizon | Git blob SHA | Forecast | Persistence baseline | Earliest *possible* future observed date | Earliest possible UTC-day-complete publication |
|---|---|---:|---:|---|---|
| 1 | `78d31625703e4563f38c460420c26134d885dff3` | 4207.98 | 4207.98 | 2026-10-12 | 2026-10-13 UTC |
| 7 | `5dbce37a27fe53d950dc4984e3522e9db3620f86` | 4225.483424799358 | 4207.98 | 2026-10-18 | 2026-10-19 UTC |
| 30 | `61ce82063472b0385e1a81c4e9137c503db6d61f` | 4183.958131173134 | 4207.98 | 2026-11-10 | 2026-11-11 UTC |

Derivation: horizon `h` counts **h strictly later, distinct daily provider observation dates**. Even with uninterrupted daily observations, the earliest h-th date is origin date + h calendar days; under the project's conservative completed-UTC-day rule, publication cannot precede the next UTC day. Actual irregular cadence can only delay this date. These are **lower bounds**, not observed provider timestamps.

As of **2026-10-24**, the h30 target is **provably not mature** under this contract; h1/h7 *could* have matured, but neither was independently settled or authenticated in this cycle. Also, h1 is the persistence model itself, so its model-minus-persistence absolute error is necessarily zero even if later settled.

Queried GitHub Actions for the exact anchoring commit; four completed successful runs report server-side `created_at` values `2026-10-12T17:13:55Z` (two) and `2026-10-12T17:14:00Z` (two). Earliest server-side presence evidence: [run 38282833039](https://github.com/islambnahmed/ai-agent-lab/actions/runs/38282833039). This proves GitHub had the commit by then, **not** when the provider actually finalized a close.

## Limits and next decision

The original provider history snapshot and original publication-time vintages were not independently fetched or authenticated in this cycle; the public provider endpoint was inaccessible through available retrieval paths. No raw vendor data were redistributed. GitHub commit presence alone does not authenticate a target, and current-vintage reconstructed closes cannot be treated as original release-time data.

**Next useful work:** obtain a provider-native archived vintage / first-publication evidence for the h1 and h7 receipts, then match exact observed-close sequences and provider measurement definitions before computing paired errors or coverage. Do not score h30 before its calendar lower bound or promote any model on a single observation. Preserve the existing frozen selector.

No changes to production forecasting, GitHub security settings, other branches, or external accounts.

## Verified CI follow-up

For the exact test commit `f8958f2ca54fc84ed54f033fa8f30d0c045c9082`, [AI Agent Lab CI run 40108462188](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40108462188) and [Lumen regression run 40108462265](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40108462265) both completed with **success**. The regression jobs on Python **3.12 and 3.13** each show **Screen synthetic Gold Lab evidence claims (normal and optimized)** as successful. The suite now contains 12 test methods (8 preexisting + 4 new); under both interpreter versions and normal/`-O` modes, this is **48 test-method executions**, not 48 distinct test cases. The GitHub CI result is verification of code behavior on synthetic claims, not real-world provider provenance.
