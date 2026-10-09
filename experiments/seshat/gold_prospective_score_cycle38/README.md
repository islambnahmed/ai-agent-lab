# Seshat cycle 38 — prospective gold scoring gate

Date: 2026-10-09. The October 2026 World Bank monthly-average gold nowcast remains **PENDING**. It was issued October 9, so it is a mid-month nowcast, not a pre-month forecast. No forecasting skill is claimed.

## Verified frozen inputs
- Original forecast Git blob SHA-1: `c9def1f51c1890e7e60e09c173aeb397b94a77bf`
- Original historical CSV SHA-256: `393793d66847bc4ccbee832424bbda8b9ececb010ca4d2da0c7e090a8b4a04d7`
- Forecast source: [October nowcast](https://github.com/islambnahmed/ai-agent-lab/blob/seshat/gold-asof-cycle28-20261009/experiments/seshat/gold_asof_cycle28/nowcast_2026_10.json)
- CSV source: [Gold monthly averages](https://github.com/islambnahmed/ai-agent-lab/blob/seshat/gold-asof-cycle28-20261009/experiments/seshat/gold_asof_cycle28/gold_monthly_2024_08_to_2026_09.csv)

## Experiment
Built `score_registry.py` and `test_score_registry.py` locally (25/25 tests passed). The scoring gate refuses modified original forecasts and source CSV, invalid month/metric, forged PDF hash, non-official URL, premature retrieval, non-PDF bytes, and invalid numeric outcomes. It does not score without a supplied future outcome. A supplied outcome remains **PROVISIONAL_UNVERIFIED** even if the PDF digest matches, because historical publication timestamp and row transcription are not independently attested.

As of 2026-10-09 13:12 UTC, evaluation returned `PENDING`. The original source CSV's `close` header denotes a **monthly average**, not a daily closing price.

Next: after November 2026 Pink Sheet publication, capture exact official PDF bytes and digest, independently verify October's gold row, store outcome separately, and score against both frozen candidates. One month is insufficient to prove skill.

Note: this README documents local work. Check branch files before claiming code is hosted on GitHub.
