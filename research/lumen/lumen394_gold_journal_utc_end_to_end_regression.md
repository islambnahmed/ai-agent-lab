# Lumen 394 — Gold journal UTC-day bug: real-product red/green CI verification

**Date:** 2026-10-24. **Authorized scope:** `islambnahmed/ai-agent-lab` only. **Implementation branch:** `sandbox/lumen-394-gold-utc`, created from `main` because `sandbox/worker-c` does not contain `products/gold-forecast`. No merge to `main`, no security-setting changes, no live market data.

## Why this cycle changed strategy

Lumen 393 reproduced an inconsistent settlement status using copied control flow and a stub. That was insufficient to establish end-to-end behavior. This cycle imported the actual `issueReceipt` and `settleReceipt` exports through a Node test inside the owning product, with 260 synthetic historical daily observations and a synthetic next-day close.

## Reproducible red/green result

1. Created `products/gold-forecast/tests/journal-timezone.test.mjs` on `sandbox/lumen-394-gold-utc` (test-only commit `9553481f25a885556d23f8ecaaff506a2ba9c19c`).
2. **Red:** `Gold Lab MVP tests` run `40122318612` failed exactly two newly introduced tests: equivalent UTC / negative-offset settlement, and the UTC-midnight boundary. Job logs showed 42 passes and 2 failures. This is an end-to-end regression test against the original production module, not a stub.
3. Applied a minimal patch to `products/gold-forecast/journal.mjs` (commit `32138ce10d251241996f501f42f354b83af8964e`). Calendar-day comparisons now use UTC dates derived from the already parsed instants for both issuance and settlement. The stored receipt timestamps are not rewritten.
4. **Green:** `Gold Lab MVP tests` run `40122346331` completed **success** on the patched commit. `AI Agent Lab CI` run `40122346329` also completed **success**.

Links:
- Red run: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40122318612
- Green gold run: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40122346331
- Green lab run: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40122346329
- Test: https://github.com/islambnahmed/ai-agent-lab/blob/sandbox/lumen-394-gold-utc/products/gold-forecast/tests/journal-timezone.test.mjs
- Patch: https://github.com/islambnahmed/ai-agent-lab/blob/sandbox/lumen-394-gold-utc/products/gold-forecast/journal.mjs

## Tests and boundaries

The regression suite covers equivalent UTC / negative-offset representations, positive-offset representations, a UTC midnight boundary (pending immediately before; matured at midnight), and equivalent issuance instants. The result establishes consistent status for this synthetic h1 case and green existing regression suites; it **does not** establish independent provider vintages, real settlement accuracy, forecast skill, or universal protection against all time/calendar problems.

**Decision:** keep this isolated, reversible fix on the dedicated branch pending owner review; do not merge automatically. A useful next test is h7/h30 parity with completed synthetic observations, followed by independent provenance verification for real prospective receipts.
