# Historical gold dataset provenance

- File: `gold_monthly_1960plus.csv`
- Rows: 801 monthly observations, 1960-01-01 through 2026-09-01.
- Source retrieved via GitHub connector: https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly-processed.csv
- Upstream origin: World Bank Commodity Markets (Pink Sheet), as identified in https://github.com/datasets/gold-prices/blob/main/datapackage.json
- Declared dataset license: ODC-PDDL-1.0 (verify upstream source terms separately before commercial redistribution).
- Columns: `date` = **month label, not price availability date**; `usd_per_troy_ounce` = average gold price in USD/troy ounce.
- The pre-1960 monthly series is deliberately excluded because annual values were repeated monthly.
- The last month in the retrieved source is 2026-09, and the file is a **snapshot**, not a live price feed.
- No claim is made that a monthly value was published on the first of its month. Backtests must apply a conservative publication lag and use only fully published months.
- This dataset does **not** conform to the daily observation schema `validate_gold_csv.py`; never silently pass monthly averages into daily-close evaluation.
- Fetch result was validated for 801 ordered monthly rows with positive finite prices before the commit.
