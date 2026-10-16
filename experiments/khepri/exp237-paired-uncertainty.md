# Khepri Experiment 237 — Paired uncertainty is not identified by marginal MAE/RMSE

Date: 2026-10-16. Source: `products/gold-forecast/reports/research-benchmark-20261012.json`, `ablation` horizon 30, `audit` (613 rows). This is a mathematical counterexample using constructed errors, **not** actual recovered forecast pairs.

## Hypothesis and adversarial test

The audit reports Price-only Ridge MAE 158.4616926, RMSE 209.9118204, and Macro Ridge MAE 168.7249485, RMSE 232.5429432. Macro's observed sample MAE is worse by 10.2632559 USD. Does this establish a reliable paired difference?

Generate two nonnegative two-level arrays of length 613 matching each model's reported MAE and RMSE exactly (floating-point tolerance). Keep each array unchanged but pair them in aligned sorted order versus reverse order. This preserves every marginal metric and the paired mean, but changes the unreported covariance.

Run `node experiments/khepri/exp237-paired-counterexample.mjs`.

## Verified results

- Both constructions: mean(Macro absolute error - Price-only absolute error) = +10.2632559 USD.
- Aligned: naive iid paired SE = 0.90369 USD; illustrative 95% interval = [8.492, 12.034].
- Reverse-paired: naive iid paired SE = 12.02385 USD; illustrative 95% interval = [-13.303, 33.830].
- The paired standard error differs by >13x despite identical MAE/RMSE and mean difference.
- A separate synthetic service-latency case (n=600) produced the same phenomenon (SE 0.48744 versus 5.90799); full independent Python tests are packaged in the cycle artifact.
- No inference is made that either constructed sequence occurred in the gold project.

## Limits and concrete next step

The archived summary establishes that Macro Ridge's **sample MAE** was worse on these 613 audit origins. It does **not** establish paired uncertainty, statistical significance, or prospective performance. The iid intervals above are purely illustrative and would not be valid for overlapping 30-close gold targets, where temporal dependence matters.

Before a model-selection claim, export common-origin rows with origin index/date, target index/date, actual, origin close, both model predictions, baseline, horizon, and vintage hash. Verify common eligibility and compute per-origin loss differences. Evaluate serial correlation and use block-bootstrap/HAC sensitivity rather than naive iid tests. Do not retune on the inspected audit.

This branch is a reversible experiment. No production selector or shared peer artifact changed.
