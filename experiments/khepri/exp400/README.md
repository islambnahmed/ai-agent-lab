# Khepri exp400 — Calendar-aware coverage and production-contract counterexample

## Question
Can a claimed-daily gold feed evade exp399's hybrid rolling cadence audit without any 4+ day gaps? Can a calendar-aware check catch it without mistaking ordinary weekends for missing data?

## Direct production evidence (main at 2026-10-23)
Fetched and executed the **actual** products/gold-forecast/data.mjs plus historical-integrity.mjs and calendar_contract.mjs dependencies from this repository. Removed only ESM import/export syntax to evaluate the same function bodies in an isolated V8 harness. Blob SHAs: data c599346f6f7f0b3eb16a0f688c9253f05745b5a9; integrity d104548e8f514903b9f7c91b3899033a85e3a914; calendar 578d433a2c2431365d879359fe1bae3d1fe3ff21.

prepareProviderHistory **accepted** all 191-row synthetic XAU/USD payloads: alternating 1/3-day, daily-then-weekly, alternating 1/7-day, and all-daily. The first three were explicitly classified calendar='observations' with an irregular-cadence warning. **This is acceptance of the declared grain='daily' feed contract, not silent mislabeling of the prediction horizon.** Production was not modified.

## New counterexample and candidate
The exp399 hybrid (20 intervals, >=50% one-day steps and <=4 gaps >=4 days) accepts alternating 1/3-day gaps: no gap >=4 days and half the gaps are daily. weekdayCoverage counts missing expected sessions between observed dates, excluding configurable weekend days. Uses a closed-form O(1) per-gap count (whole weeks plus <=6 remainder days) and sliding window; no market prices or network.

## Reproduce
Node >=22; no packages or network.

From repository root:

    node --test experiments/khepri/exp400/test_weekday_coverage.mjs
    node --test experiments/khepri/exp400/integration_production.test.mjs
    node experiments/khepri/exp400/benchmark.mjs
    node experiments/khepri/exp400/sweep.mjs

Standalone suite: **9/9 tests passed locally**; 2,000 randomized intervals compared exact closed-form counts with an independent slow day-by-day oracle using two different weekend definitions. The production integration fixture was executed through the V8 harness against fetched source; the committed Node integration test is supplied for independent reproduction, not claimed to have run in CI.

## Synthetic benchmark (seed 4002026; 1,000 trials/scenario; >=190 observations)

| Scenario | Exp399 accepted | Coverage accepted (<=7 missing weekdays / 20 intervals) | Both accepted |
|---|---:|---:|---:|
| Weekday-like + 4% random missed sessions | 999 | 1000 | 999 |
| Calendar-daily + 4% random 2-day gaps | 1000 | 1000 | 1000 |
| Alternating 1/3-day gaps | 1000 | 0 | 0 |
| Alternating 1/7-day gaps | 0 | 0 | 0 |
| Dense history + weekly tail | 0 | 0 | 0 |
| Legitimate 3-day trading week | 0 | 0 | 0 |

**Generator correction:** initial weekday generator inadvertently excluded every fifth weekday when extraClosures=0; this manufactured false positives. Fixed the generator before recording the table. Sweep shows <=4 missing weekdays rejects 50/1000 normal weekday-like sequences; <=7 rejects none in this limited synthetic family. Threshold 7 is **not** production-calibrated.

## Counterexample / limits
A legitimate three-day trading week or an extended holiday closure can be flagged as sparse. Without an authoritative source-specific market/session calendar, dates alone cannot distinguish legitimate closure from provider downsampling. This tool is **advisory-only** pending vendor-history and calendar validation. Do not auto-drop closes, rewrite dates, or turn the prototype into a hard production gate.

## Transfer
The exact expected-session counter passed tests for both Saturday/Sunday and Friday/Saturday weekend conventions. That verifies the algorithm's configurable calendar arithmetic, **not** the validity of any particular exchange calendar.

## Reusable lesson
Local daily-gap ratios do not verify a declared daily data contract. Calendar-aware expected-session coverage catches additional thinning patterns but creates a closure-calendar tradeoff. Preserve raw dates, warnings, and independent verification rather than silently correcting them.
