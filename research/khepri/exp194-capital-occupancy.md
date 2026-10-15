# Khepri experiment 194 — Capital occupancy invalidates independent-trade aggregation

Date: 2026-10-15. Offline authorized AI Agent Lab research; no trades or production modifications.

## Question

Experiment 193 measured net bps of matured forecast opportunities as independent unit-notional positions. Can that total be interpreted as investable capital return when 7/30-observation horizons overlap? No: concurrent opportunities compete for capital.

## Reusable experiment

An offline `overlap_capital_audit.mjs` prototype extends the exp193 `gold_decision_audit.mjs`. Rows carry chronological `originIndex`, `targetIndex`, `originClose`, `point`, `actual` and optional intervals. Entry uses forecast information and assumed costs, not future actuals. Up to `slots` positions coexist, each allocated 1/slots initial capital until target observation. It separately reports accepted/rejected signals, independent full-notional bps and capital-bounded bps. The test harness and code are packaged locally for reproducibility; they have not been integrated into production.

## Synthetic results

30 consecutive origins, price rises 0.1% per observed close, perfect point predictions, assumed 10 bps round-trip cost. No real gold trades or executable quotes.

| Horizon | Slots | Accepted | Naive sum (bps) | Capital-bounded (bps) |
| --- | ---: | ---: | ---: | ---: |
| 1 | 1 | 30/30 | 0 | 0 |
| 7 | 1 | 5/30 | 1806.31 | 301.05 |
| 7 | 7 | 30/30 | 1806.31 | 258.04 |
| 30 | 1 | 1/30 | 8831.73 | 294.39 |
| 30 | 30 | 30/30 | 8831.73 | 294.39 |

The 30-horizon naive sum assumes thirty simultaneous full-notional positions. Under fixed initial capital, it is not a 88.3% investable return.

## Counterexample

Two overlapping bullish opportunities earn +1000 and -1000 bps. Their independent aggregate is zero in either ordering. A one-slot policy takes the first and rejects the second; swapping the outcomes changes capital-bounded return from +1000 to -1000 bps. Thus the aggregate alone does not identify feasible capital return.

## Verification and limits

11/11 Node 22 tests passed, including 400 seeded mixed-horizon occupancy checks, no-lookahead entry selection, price scaling, cost monotonicity, malformed chronology, abstention, and positive/negative examples. An independent Python Decimal oracle matched 9/9 benchmark configurations to within 0.000001 bps.

Idealized origin-close entry, target-close exit, same-close rollover, fixed cost, additive no-reinvestment capital accounting. No slippage, borrow, financing, margin, mark-to-market, live execution or actual gold data. This is a reproducible accounting counterexample, **not evidence of a profitable strategy**.

Next: use precommitted prospective receipts and matured outcomes with independently timestamped bid/ask vintages. Do not tune parameters on held-out outcomes.
