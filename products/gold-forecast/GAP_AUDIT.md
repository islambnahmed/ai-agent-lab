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

## Remaining concrete blockers

| Blocker | Why it is unresolved / acceptance criterion |
|---|---|
| Certified multi-year daily gold benchmark | HistData M1 bid archives now support a separate multi-year study with explicit quarantines and UTC aggregation. Vendor certification and historical price vintages remain unverified |
| Exact historical macro release-time coverage | Corrected fredgraph.csv export; ALFRED monthly as-of snapshots are retrieved separately. Intraday release times and every release/revision remain uncollected |
| Predictive improvement | Historical results do not beat baseline; collect and evaluate future committed receipts before a performance claim |
| 7/30-close evidence quantity | Only 9 and 2 disjoint target windows in the retrospective audit, respectively; more data/outcomes required |
| Historical price authentication / true market calendar | Dealer feed includes weekends and gaps. Count observed closes; don't claim exchange sessions or exact settlement times |
| Real-browser/mobile end-to-end validation | App source passed DOM/network harness tests. Chromium was absent; download failed, so no successful visual/browser run is claimed |
| Public hosting | No deployment performed; model-readiness work does not imply a production site |

Source expansion and exploratory macro ablation are documented in `SOURCES.md` and the source/benchmark reports. External
source coverage and future outcomes cannot be supplied by adding code alone.
No worker lifecycle, schedules, identities or shared task state were changed.
