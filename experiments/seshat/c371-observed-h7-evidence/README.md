# Seshat C371 — First live H7 outcome observation (2026-10-23)

## What changed from C370

The previously unconfirmed [C370 read-only provider probe](https://github.com/islambnahmed/ai-agent-lab/actions/runs/39993282182) **did run successfully**. GitHub Actions job `120550222082` completed at approximately 2026-10-23 17:13 UTC. Its 7 offline tests passed, and the public Standard Bullion feed was fetched successfully. This is the first actual post-issuance observation for the H7 receipt in the lab's recorded C370 probe, not a certified historical settlement.

## Reproducible evidence

- Immutable forecast receipt: [2026-10-11-h7.json](https://github.com/islambnahmed/ai-agent-lab/blob/seshat/c370-live-observation-audit/products/gold-forecast/reports/prospective/2026-10-11-h7.json); ID `d5424cb833363c66b51e342afa99dcef56c0ab1e569f102a17877bb2ae2a8daf`.
- Source: Standard Bullion 1y XAU/USD per troy ounce daily history, the exact URL pinned in the receipt.
- Independent execution anchor: [GitHub Actions run 39993282182](https://github.com/islambnahmed/ai-agent-lab/actions/runs/39993282182), job `120550222082`; fetch receipt timestamp `2026-10-23T17:13:30.697Z`.
- Response SHA-256 `bc6d6a15fedb65c7eb66d7e97d05bc41c58941d2a303ae1814587a681fb6436e` (hash only; the raw response was **not** archived).
- Pinned origin: `2026-10-11`, `4207.98`. Current feed origin: `4207.98`, matched.
- Seven **observed** closes after origin place the target at `2026-10-18` in this provider feed, target close `4192.32`. This is an observed-series horizon, **not** a London benchmark trading-day calendar.
- Forecast point `4225.483424799358`; naive no-change baseline `4207.98`.
- Absolute error: forecast `33.16342479935793`, baseline `15.659999999999854` USD/troy ounce. Baseline is better by `17.503424799358072` (model error is `2.1177x` baseline error). The provider-current-vintage **winner is baseline**, not the model.

## The crucial vintage-coverage gap

The original receipt pinned `historyLength=324` **through** the origin and a history hash `bcbfac86e29f02576a584cdab96be7915bce5d23f622f1e0c828964eda513f9f`. The C370 current response contains `324` rows **total** and `11` rows after the origin; therefore only `313` rows through the origin are still present. At least `11` original pre-origin rows are outside the current rolling window. A matching origin price cannot prove that the original 324-row historical vintage is unchanged; the original full-prefix hash cannot be rechecked from this response.

The provider response is mutable; the response SHA alone does not prove its content later unless the bytes are preserved under an appropriate redistribution/license policy. The GitHub run timestamp proves the **probe's retrieval time**, not when Standard Bullion first published the Oct 18 value. No independently matched close-definition source was acquired. No outcome-lock or official `settleReceipt` write was made.

## Confidence and decision

**Verified:** GitHub-run execution and arithmetic on the returned current provider feed. **Tentative:** the H7 observation and baseline victory within that provider vintage. **Unproven:** release-time vintage integrity, independent price accuracy, predictive skill or a certified prospective score. One sample cannot establish general skill either way.

Do **not** promote this to a certified forecast result. Keep it as a reproducible `tentative_current_vintage` observation and preserve its provenance.

## Next discriminating experiment

1. Obtain a lawful, independently timestamped historical price series with **the same close definition** (or explicitly mark incompatible definitions) for the Oct 18 target; record release-time evidence, not just today's corrected archive.
2. On subsequent prospective receipts, retain the complete original historical vintage in authorized private storage if provider terms allow; if not, store a compact per-row hash manifest and accept that source-value recovery remains unverified.
3. Continue recording multiple **pre-registered** forecast outcomes against the no-change baseline. Treat a single H7 miss as evidence, not a final model verdict.

This C371 artifact is evidence analysis; no provider bytes, credentials, or changes to `main` are included.
