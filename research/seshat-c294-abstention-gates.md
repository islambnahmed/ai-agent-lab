# Seshat cycle 294 — Abstention gates can select the least reliable forecasts

Date: 2026-10-20. Status: **local synthetic experiment; not deployed**.

## Question
When volatility rises, should the Gold Lab suppress its 80%-target forecast interval? Evaluate *prospective* rules that only use prices and prediction errors available at each forecast origin. Challenge the cycle-293 intuition that an expanding rolling error band is evidence to suppress the interval.

## Design
- Reused the cycle-293 Gold Lab `models.mjs` blob `6bb15abe57c87bb9bc98dbc0a25e4bff5ee65b87`, chronological selection/calibration split, rolling-60 matured-error band, and identical synthetic regimes.
- Discovery seeds 401–470; untouched replication seeds 601–670. Each scenario has 70 series × horizons 1, 7, 30, 420 closes per series.
- At each audit origin, compute 20-close vs prior-60-close realized RMS return ratio using *observed past* returns only. Publish if ratio ≤2 (`vol2`).
- Compare with a plausible but flawed alternative: publish only when rolling band ≤1.5× the original calibrated band (`band15`). Also test conjunction `vol2_or_band15` (publish only when both pass).
- Outcome: coverage among **published** rolling-band intervals and percent published. Abstaining is not scored as a successful prediction. All reported coverage is synthetic and descriptive, not a guarantee.
- A price at forecast origin i+h-1 is scored only after maturity; decisions at i use past returns and labels with origin+h≤i. Prefix-invariance assertions pass.

## Replication results (seeds 601–670)

| Regime / horizon | Always publish: coverage | Volatility gate ≤2: publish share / coverage | Band-expansion gate: publish share / coverage |
| --- | ---: | ---: | ---: |
| Stationary, h=1 | 80.75% | 100.00% / 80.75% | 100.00% / 80.75% |
| Stationary, h=7 | 79.78% | 100.00% / 79.78% | 97.25% / 79.45% |
| Stationary, h=30 | 78.23% | 100.00% / 78.23% | 97.32% / 78.06% |
| 8× jump, h=1 | 59.80% | 59.57% / 73.45% | 13.79% / 16.40% |
| 8× jump, h=7 | 52.75% | 56.47% / 69.77% | 24.34% / 17.31% |
| 8× jump, h=30 | 20.52% | 38.29% / 28.15% | 80.23% / 15.12% |
| Gradual 1→8×, h=1 | 53.45% | 50.83% / 56.44% | 35.48% / 53.98% |
| Gradual 1→8×, h=7 | 48.11% | 49.32% / 50.54% | 43.72% / 46.71% |
| Gradual 1→8×, h=30 | 28.44% | 48.65% / 35.13% | 89.74% / 29.20% |

Seed-bootstrap 95% Monte Carlo intervals for `vol2` conditional published coverage under 8× jump: h=1 **72.04–74.82%**, h=7 **66.85–72.64%**, h=30 **22.82–33.66%**. These intervals quantify variation across the simulated seeds, **not market coverage**.

## Correction and causal explanation
The naive `band15` gate withholds precisely when the delayed-error rolling band finally widens to protect against a shock; it **selects early, stale, narrow intervals for publication**. At h=30, delayed labels worsen this pathology. Combining the volatility and band gates reduces the h=1 jump publish share to 3.15% while its published coverage is just 16.22%. This is not a useful risk gate.

A past-only volatility gate is less pathological in this simulator, but **still does not meet 80%** under a jump and misses gradual changes. At the exact first unseen jump, no causal detector can know the future. Selection of a gate on synthetic scenarios is not a live guarantee.

## Decision
**Reject** `band15` and its conjunction with the volatility gate. **Do not deploy** `vol2` without prospective, real-vintage validation, adequate effective sample size, and direct production `forecast()` integration. Keep the 80% band labeled as retrospective/descriptive, not a promise.

## Reproduction
The full runnable Node 22 script, independent holdout JSON, aggregate JSON, and SHA-256 manifest are in the cycle-294 artifact. No external market data, production modifications, GitHub CI, or actual `forecast()` invocation were used. This report is the only code-repository change attempted for this cycle, on an isolated branch.
