# Seshat C375 — Rolling-vintage audit without false revision claims

**Problem discovered in C374 follow-up:** products/gold-forecast/journal.mjs:settleReceipt checks hash(currentSeries.slice(0, historyLength)) against the original full-series digest. A one-year rolling feed can drop an old date when a new date arrives. Even if all retained historical prices are unchanged, the prefix comparison then fails with "Historical vintage revised / prefix missing". That error correctly quarantines settlement but **cannot distinguish** a genuine historical revision from expected window truncation. A single full-series hash cannot verify the overlapping suffix after truncation.

## Predeclared experiment and interpretation

1. Use synthetic data to test the same unchanged series with and without a rolled-off prefix. The legacy digest becomes inconclusive while a suffix commitment verifies the overlapping retained portion.
2. Store one SHA-256 digest for each *entire suffix* of the normalized historical series, with its first UTC date and the original list of dates. No raw prices are written to the repository or GitHub logs. Hashes are not encryption or proof of provider authenticity.
3. On a future provider snapshot, align on UTC dates and compare the longest overlapping suffix ending at the original origin. Distinguish full_history_match, overlap_match_prefix_unverifiable, history_dates_changed, history_values_changed, and indeterminate_no_overlap. **None** is a certified outcome.
4. For the C374 legacy receipts, report full_history_match only on an exact original-prefix match; otherwise indeterminate_legacy_prefix, never a proven revision. Do not issue replacement forecasts or select favorable re-runs.
5. Read-only CI fetch produces a derived commitment artifact with limited retention. If it expires before durable preservation, the commitment cannot serve as a future anchor. Do not claim permanent preservation from an ephemeral artifact.

## Run

node --test experiments/seshat/c375-rolling-vintage/rolling_vintage.test.mjs

node experiments/seshat/c375-rolling-vintage/probe.mjs (network required)

## Limitations

The digest chain makes rolling truncation diagnosable **only for snapshots for which a suffix commitment was actually captured and independently time-anchored**. It cannot reconstruct C374's missing original prefix retroactively. Even a full match proves equality with the committed normalized observations, not publication timing, close definition, independence, statistical skill, or tradeability. No main changes and no promotion of a provisional result.
