# Gold model gap audit — 2026-10-12

## Added and repaired

| Missing or defective part | Change / evidence |
|---|---|
| Valid live quote rejected by over-escaped Regex | Shared timestamp validator; current quote acceptance and stale/invalid rejection regression tests |
| Permissive history cleaning hid bad data | Strict source unit/grain, positive prices, duplicate conflicts, future/current-day and long-gap checks |
| Weekend/gapped rows labeled trading sessions | Preserve observations; explicitly count future provider closes; unknown date for irregular cadence |
| Longer history silently downsampled | Reject coarse daily feed; use verified native one-year endpoint, record coverage limitation |
| Live source overwrote user DEMO/CSV choice | Epoch guards; actual app tests for late fetch, late CSV and short horizon imports |
| Model choice and interval calibration shared targets | Chronological 60/20/20 windows and horizon purge |
| Three heuristics only | Ridge candidate with causal features and matured-label training |
| No data retrieval/provenance command | Python fetcher with timestamps, source URLs, raw hashes and explicit failures |
| No independent indicative quote check | Fresh Gold API quote comparison; discrepancy shown separately |
| No repeatable real-data report | Evaluation CLI, hashes, losses and per-horizon evidence |
| No prospective record / scoring | Immutable receipts pinned to code commit, private frozen vintages, pending/matured/quarantined settlement |
| Macro inputs lacked release-time alignment | FRED collector + availability/vintage feature join; no invented historical availability |
| Coverage and overlapping counts could mislead | Literal displayed-band coverage, separate disjoint counts and phase sensitivity |
| CI missed behavioral failures | Expanded Node regression suite and all-module/Python syntax checks |

## Measured real-provider sample

The native one-year snapshot contained **324 completed closes**, 2025-10-12 to
2026-10-11, with irregular cadence. Source network responses were HTTP 200 and
CORS `*`. The fresh secondary indicative quote differed from the dealer midpoint
by approximately **0.009%**, which does not validate historical prices.

| Horizon (observed closes) | Selected on earlier period | Audit MAE USD | Baseline MAE USD | Relative MAE skill | Non-overlapping target windows |
|---|---|---:|---:|---:|---:|
| 1 | Persistence | 39.41 | 39.41 | 0.00% | 65 |
| 7 | Mean reversion | 122.52 | 118.88 | -3.06% | 9 |
| 30 | Momentum | 258.77 | 226.33 | -14.33% | 2 |

**No demonstrated predictive improvement.** Negative skill means worse error
than last-close in this sample. Ridge was admitted as a candidate, not declared a
winner. Future promotion cannot rely on retuning this already inspected period.

The failed 5y request returned roughly 3-calendar-day samples while reporting
`grain=daily`. Dated historical chunk requests returned data outside their
requested bounds and repeated recent-year observations; merging them did NOT
provide five years. These attempted longer datasets were discarded; the final
report uses the native one-year snapshot only.

## Verified source expansion and exploratory ablation

The separate HistData study now contains **3,221 UTC daily observed bid closes**,
2016-01-03 to 2026-05-31. The collector counted and removed 420 identical minute
duplicates. June–August 2026 archives were quarantined for widespread conflicting
or reversed minutes; September was rejected for reversed UTC days. The terminal
UTC boundary day is omitted. No missing prices were filled and no provider
histories were concatenated. Source certification and historic price vintages
remain unverified.

Historical ALFRED exports produced **713 feature records** at monthly as-of
resolution, through vintage 2026-10-01; 1,977 price origins had all five required
non-stale macro features. Earlier broad-dollar vintage failures stay explicit.
A separate BLS calendar fetch parsed 71 scheduled CPI/PPI/employment events;
current schedules are known only from their fetch time.

| Horizon (observed closes) | Price selector | Macro Ridge MAE skill vs last-close | Macro Ridge MAE skill vs price-only Ridge | Disjoint macro audit windows |
|---|---|---:|---:|---:|
| 1 | Persistence | -2.37% | -1.07% | 642 |
| 7 | Persistence | -8.52% | -9.89% | 92 |
| 30 | Persistence | 7.66% | -6.48% | 21 |

Macro Ridge did not outperform its matched price-only Ridge comparator at any
horizon. Its 30-close improvement over last-close is an inspected retrospective
result, not demonstrated live skill or evidence for promotion. Production model
selection is unchanged. Detailed metrics and provenance are in
`reports/research-benchmark-20261012.json` and `reports/source-research-20261012.json`.

## Remaining concrete blockers

| Blocker | Why it is unresolved / acceptance criterion |
|---|---|
| Certified multi-year daily gold benchmark | HistData M1 bid archives now support a separate multi-year study with explicit quarantines and UTC aggregation. Vendor certification and historical price vintages remain unverified |
| Exact historical macro release-time coverage | Corrected fredgraph.csv export; ALFRED monthly as-of snapshots are retrieved separately. Intraday release times and every release/revision remain uncollected |
| Predictive improvement | Historical results do not beat baseline; collect and evaluate future committed receipts before a performance claim |
| 7/30-close live evidence quantity | Original live-provider audit has 9/2 disjoint windows. Separate longer-source research has 92/21; no matured prospective outcomes yet |
| Historical price authentication / true market calendar | Dealer feed includes weekends and gaps. Count observed closes; don't claim exchange sessions or exact settlement times |
| Real-browser/mobile end-to-end validation | App source passed DOM/network harness tests. Chromium was absent; download failed, so no successful visual/browser run is claimed |
| Public hosting | No deployment performed; model-readiness work does not imply a production site |

Source expansion and exploratory macro ablation are documented in `SOURCES.md` and the source/benchmark reports. External
source coverage and future outcomes cannot be supplied by adding code alone.
No worker lifecycle, schedules, identities or shared task state were changed.
