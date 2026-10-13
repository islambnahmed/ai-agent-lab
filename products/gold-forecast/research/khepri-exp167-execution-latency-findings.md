# Khepri experiment 167 — post-signal execution latency gate
Date: 2026-10-14. Status: research only, synthetic, no trades and no claim of gold-market profitability.

## Question
Does a positive close-to-close forecast imply a profitable trade if the forecast becomes available only after the origin close?

## Method
Compare idealized origin-close-to-target-mid P&L with quote-marked first-post-signal entry (long buys at ask; shorts sell at bid) and target exit (long sells at bid; shorts buy at ask). Require originAt <= signalAt < fillAt < exitAt, valid uncrossed quotes, no overlapping positions, and frozen threshold selection before audit. For long positions:

ideal = exitMid - originClose
quote = exitBid - fillAsk
ideal - quote = (fillMid - originClose) + half(entrySpread + exitSpread) + (exitMid - exitQuoteMid)

The last mark-vs-midpoint term was initially omitted; an asymmetric-quote regression test caught and corrected it.

## Reproducible synthetic findings
- 30 rising one-unit independent windows: origin close +2.00 each; point forecast +3.00 each; next post-signal quote mid +2.80; 0.20 bid/ask spread at entry and exit. Ideal P&L +60.00 units; quote-marked P&L **-30.00** units; gap penalty 84.00; spread penalty 6.00. All 30 individual winning idealized signals became quote losses.
- Zero spread, same quote gap: ideal +60.00, quote-marked -24.00. Therefore transaction costs alone do not explain the reversal.
- Control: quote gap +0.20 and spread 0.10: quote-marked +51.00. The gate does not mechanically reject all profitable hypothetical paths.
- FX-like fractional prices: ideal +0.0200, quote-marked -0.0100, demonstrating arithmetic transfer to another unit scale.
- Frozen selection chose threshold 0 on +17.00 selection quote P&L; after an unseen regime shift the same rule produced -12.00 audit quote P&L, despite +20.00 idealized audit P&L.
- 500 seeded randomized *synthetic* scenarios: all 500 P&L decompositions reconciled; 295 flipped from positive idealized P&L to negative quote-marked P&L. This fraction describes the chosen simulation distribution only, not market frequency.
- 16/16 deterministic Node tests passed after correcting the asymmetric exit-mark accounting bug.

## Decision / transfer
Do not equate forecast MAE, directional accuracy, close-to-close hypothetical profits, or per-window cost adjustments with executable strategy returns. Require timestamped issuance and first subsequent eligible bid/ask quote before considering any economic-value claim. Preserve distinct selection and audit periods. This is an audit prototype, not a promotion of any model.

## Limitations / next validation
No actual gold or FX execution quotes or fills were obtained. First eligible quotes may not be tradeable; no slippage, fees, financing, liquidity, leverage, continuous-position accounting, portfolio risk, or capital normalization. The toy quote gaps are intentionally adversarial. A real test requires time-aligned origin closes, signed/immutable forecast issuance times, quote snapshots and settlement bid/ask from a documented provider. Existing production model unchanged.

## Local reproducibility
Files in the generated reproducibility bundle: `execution-latency-gate.mjs`, `execution-latency-gate.test.mjs`, `run-experiment.mjs`, `results.json`. Run `node --test execution-latency-gate.test.mjs` and `node run-experiment.mjs` with Node >= 22. The bundle is an execution artifact; its availability in the repository depends on separate successful writes.
