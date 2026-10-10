# Khepri Experiment 127 — Delayed Labels Break Fast Calibration

Date: 2026-10-10. Scope: synthetic, reversible lab experiment; no live prices, SEO data, or deployment.

## Question
Experiment 126 assumed each outcome becomes available before the next prediction. What happens when gold settlement or SEO conversion labels arrive 5, 20, or 60 decision steps late? Can rolling 90% residual intervals be evaluated without future-label leakage?

## Method
Built `delayed_conformal.py`: an event-time queue releases outcomes only at `issue_step + delay + 1`, with calibration records selected by *prediction issue time*, not arrival order. Old late-arriving feedback cannot evict more recent eligible predictions. Duplicate labels, invalid time ordering, and nonfinite values are rejected. The algorithm predicts before scheduling the current outcome. Calibration radius is the split-conformal `ceil((n+1)*(1-alpha))` absolute-residual order statistic; under drift this is a diagnostic, not a coverage guarantee.

Deterministic NumPy benchmark: seed 20261010; 90 independent simulation runs per domain/regime; 250 calibration points, 320 evaluation points, rolling window 80, alpha=.10. Gold-like Gaussian residuals with known mean and SD 1→3; SEO-like Poisson outcomes with known mean 20→80. Three regimes each: stationary, persistent shift, 100-step shift then reversal. Compared static radius, immediate-after-decision feedback (delay 0), fixed delays 5/20/60, and randomly varied 0–60. All predictions are made without using their own outcomes.

## Measured evidence (mean fraction inside nominal 90% interval)
| Scenario | Static | Delay 0 | Delay 20 | Delay 60 | Variable 0–60 |
|---|---:|---:|---:|---:|---:|
| Gold stationary, full 320 | .9005 | .9008 | .8993 | .8992 | .9000 |
| Gold persistent shift, full 320 | .4177 | .8625 | .8326 | .7718 | .8224 |
| Gold persistent shift, first 80 | .4149 | .7440 | .6292 | .4458 | .5928 |
| Gold persistent shift, last 150 | .4174 | .9005 | .9005 | .8987 | .9009 |
| Gold reversal, last 150 | .8976 | .9021 | .9126 | .9399 | .9204 |
| SEO persistent shift, first 80 | .6194 | .8103 | .7429 | .6408 | .7244 |
| SEO reversal, last 150 | .9221 | .9239 | .9305 | .9510 | .9359 |

Gold persistent-shift early coverage falls **74.40% → 44.58%** as outcome delay rises from 0 to 60, while stationary coverage stays near 90%. Thus the difference is caused by stale feedback interacting with regime change, not delay alone. Late gold reversal coverage at delay 60 is 93.99%, higher than immediate 90.21%, but that is **not necessarily improvement**: delayed feedback leaves stale, overly wide intervals after the variance shrinks. Gold reversal mean radius: 2.88–2.90 versus static 1.66.

## Tests and counterexamples
`python -m unittest -q`: 10 tests passed, including 300 randomized availability-invariant trials, a no-lookahead prefix perturbation, a late-old-feedback ordering test, and exact agreement with Experiment 126's immediate-feedback behavior at delay zero. Stationary gold and SEO are explicit counterexamples to the claim that label delay alone necessarily ruins coverage. A reversal is a counterexample to using high coverage alone as a success metric.

## Limits
Synthetic IID draws within regimes; point forecast assumed correct; no live market data, autocorrelation, actual latency measurements, or out-of-sample economic value. Finite Monte Carlo sample (90 runs/scenario); reported percentages are descriptive, not guarantees. The code and reproducible JSON benchmark are in the local bundle, not asserted to be in this GitHub branch unless independently uploaded.

## Reusable decision
Require explicit `issued_at` and `outcome_available_at` timestamps for all forecast evaluation. Use only labels available as of each decision. Audit early-after-change coverage *and* width; compare realistic delayed feedback against an immediate-feedback oracle to quantify deployment optimism. Never interpret 90% marginal calibration as proof of reliable risk bounds during drift.
