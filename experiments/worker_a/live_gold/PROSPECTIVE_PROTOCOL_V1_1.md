# Worker A candidate XAU/USD protocol v1.1

2026-10-11 UTC. NOT active, independently timestamped, or preregistered. This revises the local v1 candidate after discovering a capture-delay defect.

Question: Does fixed three-observation linear drift beat persistence for indicative XAU/USD over a nominal one-hour horizon? Require at least 24 known observations, lookback 3, input quote age <=10 minutes. Nominal target is 3600000 ms after latest provider timestamp. Issue at first recorded capture and report effective lead.

Outcome: choose earliest supplied provider observation at or after target within 300000 ms; additionally require first capture within 300000 ms of its provider timestamp and after forecast issuance. Never replace the earliest observation with a later one when its capture is too late. Report `targetLagMs`, `targetCaptureDelayMs`, and separate missing, stale, late-capture counts. No interpolation or backfill. Both windows must be fixed before any prospective results.

Evaluate paired MAE/RMSE and missingness, select nonoverlapping forecasts using timestamps only, collapse to UTC-day votes. Candidate advantage requires >=30 selected comparisons, >=20 UTC days, >=15 decisive days, >=1% MAE improvement, and exploratory one-sided day-sign p<=0.05. Day blocks can still be dependent; no confirmatory or trading claim.

Preserve raw responses, source URL, provider and capture timestamps, hashes, Git code/protocol commit SHA, and independent first-seen evidence. Persist forecasts before target. Provider/capture times and batch completeness are not independently verified. Verify a permitted live source and reliable prospective logging before any real-market claim.
