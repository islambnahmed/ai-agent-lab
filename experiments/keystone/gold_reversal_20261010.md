# Keystone — gold monthly forecast reversal audit (2026-10-10)

## Result (retrospective extension; not a live prediction)
The previous fixed **2-month availability embargo / 12-month log-trend** model beat the last-known-price baseline by **28.8917% MAE** over Apr 2024–Mar 2026 in an already-inspected 24-month window. Holding that same model fixed and extending to **Apr–Sep 2026** reverses the sign:

- 6 target months, 2 trend-model wins.
- Baseline MAE: **333.9183 USD/troy ounce**.
- Trend-model MAE: **523.1385 USD/troy ounce**.
- Trend relative improvement: **−56.6666%** (worse).
- Trend forecast rose relative to baseline in all 6 target months, while actual exceeded baseline in only 2.

This is a **significant qualitative failure of regime transfer**, not a statistical significance claim. Six targets are too few to establish a general predictive result.

## Source and reproducibility
- Frozen prior script and parameters: Keystone cycle-11 artifact `keystone_cycle11_regime_robustness.zip`; source extract Jan 2018–Mar 2026, SHA256 `c70542fe109d09f00891b14a621449b8c8674dadb1c01ef4cd02b7681abfea78`. Its original data were attributed to IndexMundi/World Bank, and publication-time vintages were **not** verified.
- World Bank [July 2, 2026 Pink Sheet](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Pink-Sheet-July-2026.pdf), page 2 Gold row: Apr 4721, May 4587, Jun 4228 USD/toz.
- World Bank [October 2, 2026 Pink Sheet](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Pink-Sheet-October-2026.pdf), page 2 Gold row: Jul 4073, Aug 4411, Sep 4319 USD/toz.
- The 2025-03–2026-03 values in the 19-row fixture were copied unchanged from the previous artifact. The six new official monthly values are rounded to the nearest dollar, unlike the prior two-decimal secondary extract.
- Gold prices are **monthly averages, not month-end closes or executable trading prices**.

Run `python experiments/keystone/gold_forward_reversal_20261010.py experiments/keystone/gold_2025-03_2026-09.csv`, then `python -m unittest discover -s experiments/keystone -p 'test_gold_forward_reversal_20261010.py'`.

## Causal and evidence limits
This audit was computed in October 2026, after all six outcomes were public. Although model parameters were frozen in a previous artifact, this is **not** a prospective preregistered test and does not establish point-in-time source availability. Do not choose a replacement model using these six months and then claim they are untouched holdout. A real next step is a timestamped forward prediction ledger with immutable predictions and source vintages, plus future outcomes. This failure is a reason to avoid promising gold-price forecasting accuracy.
