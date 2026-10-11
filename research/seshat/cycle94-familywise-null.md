# Seshat cycle 94 — familywise horizon-selection negative control
Date: 2026-10-12 (Africa/Cairo)

## Question
Does allowing a user to inspect three forecast horizons (1, 7, 30 sessions) increase the probability of observing a misleading apparent backtest win, even when future returns are unpredictable?

## Method
Reused the unchanged products/gold-forecast/forecast.mjs from the cycle92 branch (blob 4e4a2438608955e17f3d0e3dd66764aa5cb6c9b4). Simulated 1,000 independent 500-session weekday price histories (seeds 1–1000) using iid N(0,0.01^2) log returns, initial price 2500. For each series, evaluated all three horizons on the SAME history, then counted whether ANY horizon reported beat=true and whether ANY horizon exceeded 5% relative MAE gain. Independent replication used seeds 10001–10500 (n=500). No actual gold data were used.

## Results
| Metric | Seeds 1–1000 | Independent seeds 10001–10500 |
| --- | ---: | ---: |
| Any of three horizons reported a win | 460/1000 = 46.0% | 226/500 = 45.2% |
| Any horizon reported >5% relative MAE gain | 158/1000 = 15.8% | 79/500 = 15.8% |
| Empirical 95th percentile of max gain | 11.45% | 14.80% |
| Horizon 1 beat | 194/1000 | 105/500 |
| Horizon 7 beat | 203/1000 | 95/500 |
| Horizon 30 beat | 253/1000 | 123/500 |

With 500 sessions, the existing 80/20 audit split has 100 holdout sessions. For horizon 30, forecast.mjs reports 71 overlapping audit origins but permits only floor(100/30)=3 disjoint target windows. Disjoint does not imply independent.

## Interpretation
A user can find an apparent historical winner on an unpredictable series nearly half the time by examining three horizons. This is NOT a 46% conventional statistical false-positive rate: beat is a descriptive comparison without a predeclared significance threshold. The empirical max-gain threshold is calibrated ONLY for this synthetic null and is not valid for live gold markets, structural breaks, or altered code.

## Decision
Do not show the historical beat flag as a claim of predictive skill. Label it descriptive, require pre-registered/frozen prospective predictions and enough disjoint target windows, and report simultaneous-horizon selection risk. Do not use the 95th percentile above as a universal market threshold.

## Verification
Node v22.16.0, four unit tests passed. Reproducible local scripts/results archived in cycle94 artifact. No real-data, production, or deployment verification claimed.