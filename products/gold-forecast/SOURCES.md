# Global XAU/USD source audit — 2026-10-12

Scope: global gold in USD per troy ounce. Every price series retains its own
measurement and clock; sources are evaluated separately. No inferred local
currency, retail premium, or invented market volume enters the project.

## Inputs acquired and implemented

| Input | Actual source / measurement | Accepted use |
|---|---|---|
| Multi-year gold | [HistData](https://www.histdata.com/f-a-q/), XAUUSD M1 bid OHLC; fixed EST UTC-5 without DST per provider documentation | Aggregate last observed minute close per completed UTC day, separately from Standard Bullion. Validate bars and requested periods; retain gaps. Identical duplicate minutes are counted and removed; differing/reversed minutes quarantine the affected UTC day. More than two affected days quarantine the entire archive period |
| Real 10y yield | [DFII10](https://fred.stlouisfed.org/series/DFII10), percent | Current FRED history and historical monthly ALFRED vintages |
| Nominal 10y yield | [DGS10](https://fred.stlouisfed.org/series/DGS10), percent | Same availability contract |
| Broad dollar | [DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS), Jan 2006=100; **not ICE DXY** | Current history; only actually returned historical vintages. Earlier failed exports are recorded, not reconstructed from today's values |
| US CPI | [CPIAUCSL](https://fred.stlouisfed.org/series/CPIAUCSL), seasonally adjusted index | Index and derived 12-month percent change using two observations in the same historical vintage |
| Policy-rate context | [DFF](https://fred.stlouisfed.org/series/DFF), effective federal funds rate, percent | Same availability contract |
| Scheduled economic events | [BLS iCalendar](https://www.bls.gov/schedule/news_release/bls.ics), CPI/PPI/employment releases | Timezone converted with America/New_York DST. This downloaded calendar is known only from fetch time; it is not backdated into past forecasts |
| Long monthly gold context | [World Bank Pink Sheet](https://www.worldbank.org/en/research/commodity-markets), 801 monthly rows, Jan 1960–Sep 2026, USD/troy oz | Separate monthly research context. Never relabel as daily or forward-fill into the daily target |

The World Bank workbook's Description sheet states that gold changed from
London afternoon-fixing monthly averages to **spot averages from June 2025**.
This is a measurement break, not a homogeneous unchanged 66-year daily series.
The original workbook remains local; its source/hash and inspection are recorded
in `reports/source-alternatives-20261012.json`.

FRED's public CSV address is `graph/fredgraph.csv`, not `graph/graph.csv`.
Historical-vintage CSV is `graph/alfredgraph.csv`. [ALFRED documentation](https://alfred.stlouisfed.org/help/downloaddata)
distinguishes observation dates, vintage dates and initial-publication dates.
The collector checks the returned vintage header, rejects nonfinite/future
values and preserves missing cells. Multi-column exports can include dates
before the requested start; the parser explicitly filters the union.

Monthly as-of snapshots are usable only after `23:59:59.999Z` of their vintage
date, a conservative day-level policy. This does not claim the value first
became available at that instant. Between snapshots a genuinely newer release
may be missing. Current downloaded historical values are never used as if they
were known at a past origin.

## Alternatives actually checked

| Source | Observed result | Decision |
|---|---|---|
| Standard Bullion native 1y | 324 completed irregular closes; long/date-range attempts failed their requested contracts | Existing live workflow retained; no invented 5y history |
| Gold API | Fresh secondary indicative quote acquired earlier | Live sanity check only; does not authenticate historical prices or upstream independence |
| SD Bullion 2025 daily tables | 255 published rows. Aug 25 and Dec 26 have both AM and PM quoted prices although listed as London auction holidays | Quarantined as an unverified fixing source. No table rows used for training |
| ICE/LBMA | [Official auction/holiday documentation](https://www.ice.com/iba/lbma-precious-metals); benchmark data subject to license | Calendar applies to the London benchmark, not every vendor bid feed. Do not substitute it for HistData's observed-close cadence |
| Bank of England XUDLGPD | Gold publication ceased June 2017; historical export request returned 403 | Not a current daily-price replacement |
| Dukascopy public legacy archive | Probes returned 429; current documented S3 export requires requester-pays access | No rate-limit workaround or paid access attempted |
| Stooq | Browser verification / unavailable CSV route | No usable downloaded history; no verification bypass |
| [CFTC disaggregated COT](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm) | Official annual futures-position archives identified; actual 2026 ZIP request returned 403 | Optional positioning candidate. Needs report-release dates, holiday exceptions and revision handling before historical joins |
| [World Gold Council ETF flows](https://www.gold.org/goldhub/data/gold-etfs-holdings-and-flows) | Monthly downloadable workbook identified; actual download returned 403 | Optional demand candidate; no values invented or backdated |
| [FOMC calendar](https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm) | Official schedule read through web retrieval; direct downloader returned 403 | Reference found, automatic importer not implemented. Current schedules cannot stand in for historical schedule vintages |

## What still needs evidence

1. Intraday release times and all daily macro revisions; monthly vintage samples
   are a useful conservative first dataset, not complete release-by-release data.
2. A second authenticated historical price source with matching close definition,
   and frozen historical price vintages. Different publishers may share upstreams.
3. Fresh daily historical updates for the research archive; the collector only
   downloads completed local months and conservatively omits the terminal UTC
   boundary day. June–August 2026 archives had widespread ambiguities and were
   quarantined; September contained reversed UTC days and was rejected. Live
   quotes and a stale historical research archive are distinct.
4. Optional COT/ETF/central-bank demand, futures volume/open interest and news
   inputs require actual public files plus publication-time history before use.
   No complete worldwide spot-volume field exists in these acquired feeds;
   HistData's zero volume is unavailable data, not zero trading activity.
5. Future forecast outcomes to test improvement. New data and an inspected
   retrospective result cannot establish live predictive skill.

`research-model.mjs` is a frozen exploratory Ridge ablation, with 400 eligible
matured labels, penalty 20, five causal price features and five macro features.
Its price-only ablation shares the exact eligible origins and labels. No audit
retuning or production promotion happens automatically. Provenance, exclusions,
coverage and numerical results are in the committed reports.

Raw vendor files remain under ignored `data/`; reports redistribute source URLs,
hashes and derived metrics. Public availability is not assumed to grant benchmark
redistribution rights. Government macro sources retain official attribution.
