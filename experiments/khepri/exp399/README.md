# Khepri exp399 — local cadence audit of claimed-daily feeds

## Research question
Can the Gold Lab's production daily-feed guard be bypassed by a provider that serves a mixture of daily and weekly observations? Can a better guard reject sparse stretches without falsely rejecting legitimate weekday-like markets?

## Actual repository code inspected
`products/gold-forecast/data.mjs` at `main` (2026-10-23) has a global ratio check in `prepareProviderHistory`: `oneDaySteps / (series.length - 1) < 0.5`. `prepareHistory` rejects gaps strictly greater than seven calendar days, but a seven-day weekly segment is allowed and classified as irregular observations. The prototype here is **not wired into production**.

## Reproduce
Node >=22, no packages or network:

```bash
node --test test_cadence_window.mjs
node benchmark.mjs --write
```

8/8 tests pass. Four scenarios x 1,000 seeded synthetic trials = 4,000 trials. Each trial has roughly 190 observed dates. The original global guard is reproduced exactly as a date-gap ratio; the rolling-window variants and hybrid are implemented independently.

## Counterexample
193 closes covering 360 days: 165 consecutive daily observations followed by 28 weekly intervals. The original global one-day-step ratio is 164/192 = 85.4%, so it passes the claimed-daily guard, even though the most recent 28 intervals are all weekly. No gap exceeds the seven-day hard limit. The production calendar classifier would flag irregular cadence and suppress the projected calendar target, but would **not reject the feed as daily**. This is a contract-acceptance false negative, not evidence of incorrect predictions.

## Benchmark outcomes (accepted out of 1,000)

| Synthetic generator | Existing global >=50% | Rolling 20-step >=50% | Rolling >=65% | Hybrid: rolling >=50% AND <=4 gaps of >=4 days in any 20-step window |
|---|---:|---:|---:|---:|
| Weekday-like, 4% random missed sessions | 1000 | 1000 | **805** | 1000 |
| Daily-like, 4% random two-day gaps | 1000 | 1000 | 1000 | 1000 |
| Long weekly tail | 1000 | 0 | 0 | 0 |
| Alternating 1-day / 7-day gaps | 1000 | **1000** | 0 | 0 |

**Falsified initial idea:** simply increasing the local daily-density threshold from 50% to 65% catches alternating sparse feeds but incorrectly rejects 195/1,000 legitimate weekday-like synthetic sequences. The hybrid detector uses a conservative 50% local density check plus a separate long-gap clustering check. It passes all 2,000 dense-feed cases and rejects all 2,000 sparse-feed cases in this *limited* generator family. This is not a calibrated production false-positive rate.

## Limitations / next steps
- Not tested against real vendor histories, exchange holiday calendars, market closures, or source revisions. An unusual legitimate closure schedule could trigger the hybrid detector.
- A provider can manipulate dates or supply fake dense prices; cadence checks cannot prove authenticity or predictive quality.
- The chosen window (20), long-gap definition (>=4 days), and limit (4) are hypotheses, not validated operational thresholds.
- A 4-day/7-day hybrid can miss repeated 2–3 day downsampling; extend adversarial generators before considering production integration.
- Reproduce against actual `prepareProviderHistory` and market calendars in an integration branch before deployment; keep `main` unchanged.
