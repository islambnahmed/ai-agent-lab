# Khepri experiment 165 — forecast accuracy ≠ economic value

**Date:** 2026-10-13. **Status:** tested synthetic research prototype; no trading, no production integration.

## Question
Does a model with lower price MAE necessarily offer positive economic value after execution costs? Can a threshold chosen without audit leakage still fail out of sample?

## Reproducible evidence
Local Node.js tests: 9/9 passed. Artifacts and source hashes are in the local reproducible bundle.

1. **Perfect synthetic gold forecast:** 20 sequential one-close opportunities with alternating +$0.30/-$0.30 moves per troy ounce. Forecast MAE $0 versus persistence MAE $0.30. A long-only policy trades 10 positive signals. At assumed $0.50 round-trip cost per ounce, net P&L **-$2.00**; at zero cost **+$3.00**. Explicit abstention gate selects `abstain`.
2. **Out-of-sample regime shift:** 20 +$2 selection moves, then 20 -$2 audit moves; forecast always predicts +$2. Selection-only threshold = $1. At $1 cost, selection P&L **+$20** and audit **-$60** (20 trades); abstention $0. Chronology alone does not ensure economic transfer.
3. **FX transfer:** Perfect synthetic FX forecasts with +/-0.0005 moves and 0.0008 cost lose **0.0030 quote units** over 10 trades.
4. **Validation:** reject overlapping windows, malformed indices and overlapping selection/audit labels; serialize abstention as the stable string `abstain`.

## Implication
`products/gold-forecast/forecast.mjs` optimizes MAE, not realizable trading P&L. The 2026-10-12 readiness report's 7- and 30-observation selected models had higher audit MAE than persistence; h1 was persistence. Neither fact establishes economic profitability. No real execution-cost backtest was performed.

## Next falsification
Use frozen actual row-level gold observations, nonoverlapping origins and purged chronological splits; pre-register transaction cost and threshold grid; compare against both flat and always-long on identical windows. Synthetic perfect fills omit spread dynamics, financing, borrow fees, slippage, liquidity, taxes and market impact. No trading action or production change.

## Local artifacts (verified)
`cost-aware-gate.mjs` SHA256 `758edfa86d0c5a4f17266d11388b989c992df7c1bc5e6fa94f6e13ffd24c496d`.
`cost-aware-gate.test.mjs` SHA256 `feca971db385631d01ea843a3b027fa639e0138709cd3d35868c92e1df333ed4`.
`results.json` SHA256 `0705d3322f424051fb285411dd1ae69b226f96a41f53b19eed95b258246e6848`.
