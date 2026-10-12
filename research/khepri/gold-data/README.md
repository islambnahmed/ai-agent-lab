# Gold historical backtest data contract (Khepri)
This is an ingestion/evaluation scaffold, **not historical market data**. Never treat generated examples as real prices.

## Required dataset
Place licensed/attributable historical observations at `research/khepri/gold-data/observations.csv`:
`date,close,source,asset,currency,unit,observed_at_utc`
- `date`: ISO exchange/session date, strictly increasing, unique.
- `close`: finite positive price (no forward-filled missing sessions).
- `source`: exact dataset/provider identifier; keep retrieval URL and license in `provenance.md`.
- `asset`: e.g. XAUUSD spot, not silently mixed with COMEX futures or local retail quotes.
- `currency` and `unit`: e.g. USD and troy_ounce.
- `observed_at_utc`: UTC timestamp when value was available; must not be after prediction cutoff for training.
- Record timezone, revision policy, corporate/provider transformations, missing days, and calendar in provenance.
- Never commit credentials, paywalled data without rights, or data of unknown license.

## Evaluation protocol
Use a chronological holdout, walk-forward origins, naive last-close and drift baselines, MAE and directional accuracy, sample sizes and confidence intervals. All predictors must only use observations with `observed_at_utc` <= forecast issue time. Freeze horizon and prediction timestamp before evaluating. Keep an untouched final test period. Do not use a randomly shuffled split.

## Current status
No genuine historical prices are included in this commit. First obtain a legally reusable source with verifiable provenance, then ingest and validate it. The benchmark below is deliberately limited to input validation until such data exists.
