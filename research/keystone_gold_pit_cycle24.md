# Keystone: release-aware gold backtest (2026-10-09)

## Scope
A conservative month-first forecast audit using the nine **rounded, PDF-checked** World Bank Gold observations for January–September 2026. This is a descriptive proof of the point-in-time evaluation contract, not evidence of forecasting skill or investment performance.

## Core finding
At 00:00 on the first day of month M, the previous month's World Bank average is not yet published. The latest verified monthly price is normally M-2. A forecast for M therefore needs a **two-month observation horizon** when using only this source. Never silently use M-1.

## Paired results (six forecast origins, April–September 2026)
- Last-published-value baseline: MAE **$334.00 per troy oz**.
- Mean log-return extrapolation across the actual two-month gap: MAE **$497.46 per troy oz**.
- Candidate was **48.94% worse** in this tiny descriptive sample. No inference or skill claim is warranted.
- March origin has only one released training observation; exclude from paired model comparison. Seven total baseline origins, six paired.

## Validation
- 12 new tests and 12 previous vintage-guard tests passed locally (24 total).
- Tests include future-target mutation invariance, same-day publication exclusion, shifted publication dates, target missing => fail closed, paired-origin comparison, invalid windows, duplicate months.
- Source ledger SHA-256: `59c3f21a7c94b59388ff18b6bc7ccb3950d6e4a3f03562f7a9da28b53a746325`.
- Code/report bundle was generated locally in the automation run; do not claim it is committed unless a separate code write succeeds.

## Limits and next action
Nine rounded observations only; the source PDFs' printed release dates are not exact intraday timestamps. Historical revisions are not fully captured. The official monthly XLSX binary download was attempted and failed in this environment; don't repeat the same blocked route without changing tools. Next: integrate an explicit availability timestamp and vintage ID into the existing `tools/gold_walkforward.py` input contract before using it for website accuracy claims.
