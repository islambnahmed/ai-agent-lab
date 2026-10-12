# Daily gold historical closes — provenance and cautions

- File: `gold_daily_2001_2026.csv`, 6,420 rows.
- Source: https://github.com/tohaitrieu/market-history/blob/master/data/commodities/GOLD/GOLD-D1.csv
- Retrieved raw from: https://raw.githubusercontent.com/tohaitrieu/market-history/master/data/commodities/GOLD/GOLD-D1.csv
- Original fields: `Asset,TimeFrame,Time,Open,High,Low,Close,Year,Quarter,Month,Week`. Extracted the ISO date from `Time` and original `Close` without forward filling.
- Range: 2001-06-03 through 2026-02-05. **Not current to October 2026.**
- Source repository README states "Public domain - free to use for any purpose." However, original upstream quote provider and independently verifiable licensing are **not documented**. Treat redistribution permission as claimed by repo maintainer, not independently verified.
- 6,420 rows validated: strictly increasing unique dates, finite positive OHLC and low <= open/close <= high.
- Original timestamp is often `21:00`, but timezone and precise session convention are **not verified**; normalized `date` is a source label, not guaranteed exchange calendar.
- Gold symbol `GOLD` and OHLC are not independently confirmed to be exactly equivalent to XAU/USD spot closes from Standard Bullion used by MVP. Do not merge sources without cross-check.
- The dataset is **retrospectively collected**, with no as-of publication audit. Use only for exploratory research; do not assert live trading skill, prospective validity or investment recommendations.
