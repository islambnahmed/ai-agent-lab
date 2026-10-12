# Worker A — Cycle 86: historical XAU/USD benchmark path

Date: 2026-10-13. Authorized repo: `islambnahmed/ai-agent-lab`, branch: `sandbox/worker-a`.

## Decision and capability
Following cycle 85's synthetic-only baseline experiment, prioritize *real 1-minute historical data* with timestamp hygiene over further polishing the browser ledger. Found a publicly described six-month 1-minute XAUUSD OHLCV sample from getdata.finance, advertised on https://github.com/getdata-finance/xauusd-1m-ohlcv-metals-historical-data . Vendor describes the data as broker-CFD mid quotes, not a centralized exchange or the gold-api.com quote used by the demo. Vendor terms: https://getdata.finance/datasets/xauusd . **Do not merge quote sources or present this as canonical executable spot prices. Do not redistribute raw dataset.**

Created and published to this branch:
- `experiments/worker_a/gold_site/gold-site-offline-eval.mjs`: 75m persistence vs fixed 30m momentum, chronological holdout, explicit missing targets and maturity, no future-value interpolation.
- `experiments/worker_a/gold_site/gold-site-offline-eval.test.mjs`: seven deterministic tests.
- `experiments/worker_a/gold_site/gold-site-ohlcv-adapter.mjs`: validates 1m OHLCV source CSV and converts close-price timestamps from *bar open* to *bar end* (+60 seconds). Otherwise the benchmark would use a bar's future close as if it were available at bar open.
- `experiments/worker_a/gold_site/gold-site-ohlcv-adapter.test.mjs`: four new tests for look-ahead timing, malformed OHLCV, no gap filling, UTC timestamps.

## Verification
On local Node.js v22.16.0, 51/51 tests passed across existing cycle-84 local regression suite (40), offline evaluation (7), and adapter (4): `node --test *.test.mjs`. **This is a local test run; GitHub CI and live browser were not run.**

All four published GitHub blobs were re-fetched from `sandbox/worker-a`. Their blob SHAs exactly matched `git hash-object` of locally tested files:
- offline eval `fa05521813c8f23bf58c78d7139c3ba0355da9b2`
- offline eval tests `173ab6526d9feb2d70d1c22bd71ea6023a19bc7d`
- OHLCV adapter `0f9fcd1a9f8711e2c3e26620672d7c42848991de`
- adapter tests `f08be5737b7502940aec436a5fe75c0dd7ca7bc0`

## Blocker and limitations
The public sample CSV was **not downloaded**: container download failed, and local network requests failed DNS resolution. Therefore there are **no actual historical gold benchmark results yet**. No paid feed, account, or external repository write was attempted. The bar-end label is an *earliest theoretical availability*, not proof of provider delivery latency; independent timestamp witnessing and prospective forecasting remain missing.

## Reproduce when a lawful sample becomes accessible
```bash
node gold-site-ohlcv-adapter.mjs XAUUSD_1m.csv > observed.csv
node gold-site-offline-eval.mjs observed.csv --stride-minutes 75
node --test gold-site-offline-eval.test.mjs gold-site-ohlcv-adapter.test.mjs
```
Interpret MAE/RMSE and coverage jointly. No model selection on the holdout; evaluate distinct months/market regimes separately and disclose missingness. Even a positive retrospective result is not evidence of prospective predictive skill.

## Next decision
Get a permitted, timestamped XAU/USD 1m sample via a functioning data-access path. Run fixed-protocol benchmark, report exact date range, count, coverage, paired errors and per-regime stability. Separately keep the pending ledger retention fix tracked; do not conflate UI integrity with predictive ability.
