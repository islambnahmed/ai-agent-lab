# Gold Lab v2 — model readiness

Arabic RTL research dashboard, four lightweight models, validated provider data,
separate selection/calibration/audit periods and immutable prospective receipts.
This implementation runs without GPT/Claude, a paid API, or third-party runtime
packages. It does not establish predictive skill or investment profitability.

## Run and reproduce

From this directory, with Node >=22 and Python >=3.10:

```bash
npm test
npm run data
npm run macro
npm run evaluate
python3 -m http.server 8000 --bind 127.0.0.1
```

Open http://127.0.0.1:8000. The site fetches provider data directly. CSV and DEMO
are explicitly labeled. Failed network requests never substitute synthetic prices.
The fetch manifest now records both the raw HTTP SHA-256 and the exact SHA-256
of each serialized local JSON snapshot. Evaluation and prospective issuance reject
missing, stale, or mismatched snapshot files; run `npm run data` to regenerate
older manifests without `storedSha256`. This verifies local file/manifest binding,
not provider authenticity or independent price accuracy.

The evaluation command produces `reports/readiness-20261012.json`; raw provider
snapshots stay in ignored `data/`. Macro fetch writes its source-status report.

After committing the code, fetch a fresh snapshot and issue future forecasts:

```bash
npm run data
npm run issue
```

Commit the new `reports/prospective/*.json` receipts **before** target closes are
available. Later: `npm run data && npm run settle`. Settlement is written to
ignored `runs/settlements.json`; it cannot edit receipts. Preserve local
`data/vintages/` until settlement, because a rolling one-year feed cannot
reconstruct the exact original vintage. Source revisions quarantine outcomes.
A receipt hash detects changes; the externally timestamped Git commit anchors
issuance. No task schedule or worker configuration is changed by these commands.

## Observation and source contract

- Gold is XAU, USD per troy ounce. Historical `grain` must explicitly be daily;
  source attribution is required. Bid/ask remain separate dealer quote products.
- Reject invalid/non-positive values, conflicting duplicates, invalid times,
  future timestamps and >7-calendar-day gaps. Sort dates and remove provisional
  current UTC day observations. UTC completion is a conservative convention,
  not a verified exchange settlement timestamp.
- Keep valid weekend prices. Never forward-fill missing prices or silently drop
  weekends. If actual cadence is irregular, horizons mean **1/7/30 future observed
  provider closes**. No calendar target date is invented. Otherwise show an
  approximate calendar/weekday target; holiday calendars remain unverified.
- Reject a claimed daily source when fewer than half its successive rows are
  one calendar day apart: this detects the observed 5y downsampling contract
  failure. It is a data-quality heuristic, not source authentication.
- Live quotes require positive uncrossed bid/ask, correct unit and fresh explicit
  timestamps. Gold API provides an indicative second quote; prices and timestamps
  must be near one another. Different products and shared upstream sources can
  still agree; this check does not validate the historical dataset.

## Models and evaluation

`models.mjs`: persistence, damped momentum, geometric mean reversion and Ridge.
Ridge predicts the horizon log return from trailing 5/20-close returns,
20/60-close mean deviations and 20-return volatility. It standardizes using
training rows only, regularizes coefficients at alpha=20, uses up to 400 matured
training labels and caps predicted log returns at +/-0.20. During warmup it
explicitly falls back to last-close. These are fixed exploratory settings.

`forecast.mjs`: chronological 60/20/20 periods. Model selection uses the first
period; interval calibration uses the second; the last is for descriptive audit.
Purge h-1 origins at each boundary so target labels do not cross back. At every
origin, the fit sees only already observed prices and matured training labels.
The 80% finite-order calibration band is empirical; neither independence nor
coverage guarantees are asserted. Report MAE, RMSE, MAPE, direction accuracy,
relative MAE skill, literal interval coverage, disjoint counts and phase coverage.
Non-overlapping windows are **not statistically independent**. The historical
period was examined by previous implementations, so this is not a fresh blind
validation of v2. Prospective observations after code/receipt commits are needed.

Macro inputs use `feature-store.mjs`: values join only when `availableAt <=
originAt`, with explicit source/vintage and staleness. The corrected FRED
`fredgraph.csv` export retrieves full current-vintage history; it stays available
only from its actual fetch time. ALFRED `alfredgraph.csv` exports supply separate
historical monthly as-of snapshots, conservatively available at the end of the
requested vintage day. They are not an intraday release calendar.

The separate research pipeline downloads HistData XAU/USD M1 bid archives,
aggregates completed UTC days from fixed EST input, and explicitly quarantines
ambiguous repeated-clock days. It never fills absent prices or concatenates
unrelated providers. The experimental macro Ridge ablation uses real/nominal
10-year yields, the broad dollar index (not DXY), same-vintage CPI annual change,
and effective Fed funds. Training labels must mature before each origin. Its
price-only comparator uses identical eligible origins and training rows.
Production model selection is unchanged; the inspected research period cannot
justify automatic promotion.

```bash
npm run research-data       # public source downloads; raw cache remains local
npm run research-evaluate   # multi-year price benchmark + fixed macro ablation
npm run calendar            # official BLS scheduled releases, known from fetch
npm run source-tests        # no network access
# rebuild already downloaded archives without retrying unavailable sources:
python3 scripts/collect_research.py --offline
```

Read `SOURCES.md` for accepted, quarantined and unavailable sources, measurement
changes, optional inputs and the precise remaining gaps. Research data under
`data/` is ignored by git; reproducible download commands and derived reports
are committed. Results record source hashes and an implementation hash.

## Sources and redistribution

- [Standard Bullion API](https://standardbullion.com/gold-price-api)
- [Standard Bullion market data](https://standardbullion.com/market-data)
- [Gold API](https://gold-api.com/docs)
- [FRED DFII10](https://fred.stlouisfed.org/series/DFII10)
- [FRED DGS10](https://fred.stlouisfed.org/series/DGS10)
- [FRED broad dollar](https://fred.stlouisfed.org/series/DTWEXBGS)
- [FRED CPI](https://fred.stlouisfed.org/series/CPIAUCSL)
- [FRED real-time periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)

Keep attribution visible. Do not bulk redistribute raw provider feeds. Reports
contain hashes, derived metrics and small forecast receipts, not raw history.

## Integration provenance

`historical-integrity.mjs` and its original tests build on Seshat commit
`62df721943584b9df11a6602808924b32cf1a32a`, with stricter clock/offset checks.
`calendar_contract.mjs` builds on Khepri commit
`7329ec0ebac1353e54108124cfb26b9615cdf7aa`. Production cadence now refuses to
label irregular observed rows as a known calendar horizon. Prior UI race/coverage
hardening from PR #2 is retained, with regression tests of the actual app source.

See `GAP_AUDIT.md` for completed fixes, measured results and remaining blockers.
