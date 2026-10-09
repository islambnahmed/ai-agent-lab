# Gold point-in-time backtest (Keystone)

Run `python -m unittest discover -s tests -p 'test_gold_point_in_time.py'`.
CSV columns: `date,close,available_at`; the third field MUST be the verified
actual release time, including timezone offset (e.g. `2025-01-02T00:05:00+00:00`).
Do not fabricate release timestamps for real datasets. Backtest compares
last available close vs expanding historical log-return drift. No model is
promoted without an untouched holdout and a meaningful edge over persistence.

`python tools/gold_point_in_time.py path/to/verified_prices.csv --horizon 7`

This tool intentionally refuses files without release metadata. A series of
monthly averages is not interchangeable with daily XAU/USD spot closes or
gold futures settlements. The observed target is evaluated after the fact.
