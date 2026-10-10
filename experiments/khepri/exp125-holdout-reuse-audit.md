# Khepri Experiment 125 — Adaptive Holdout Reuse / False Winners
Date: 2026-10-10. Scope: synthetic lab simulation only.

## Question
Can selecting the best of many candidate predictors on the same validation holdout make objectively inferior predictors appear to beat a baseline? Does the failure transfer from continuous gold-return-like targets to binary SEO-conversion-like targets?

## Reproducible setup
Deterministic NumPy simulation; 1,500 independent runs per scenario, validation n=64, untouched test n=64. Candidate counts K=1,8,32,64. Baseline: 0 for standard-normal continuous targets, 0.20 probability for Bernoulli(.20) conversions. Null candidates produce independent noise forecasts: Normal(0,.40) for continuous, clipped 0.20+Normal(0,.075) for binary. All null candidates are inferior to the baseline in expected squared/log loss. Select the candidate with smallest validation loss; evaluate that same selected candidate on the untouched test. Metrics report baseline loss minus candidate loss (positive = apparent improvement).

## Observed evidence
Gold-like continuous null, K=64: 95.933% of runs showed a validation win, but only 5.267% showed a test win; mean validation improvement +0.070286 (95% simulation CI +0.067979 to +0.072593); mean untouched test improvement -0.161177 (CI -0.166209 to -0.156145). At K=1, validation win rate was 5.067%.
SEO-like binary null, K=64: 100% showed a validation win, but 23.333% showed a test win; mean validation improvement +0.037330 (CI +0.036823 to +0.037838); mean untouched test improvement -0.020871 (CI -0.022305 to -0.019436). At K=1, validation win rate was 21.867%.

## Counterexamples / boundary conditions
64 exactly duplicated candidates gave *identical* results to K=1 for both domains, showing effective independent search diversity matters, not the raw number of candidates. With a genuinely informative synthetic feature x and y=.70*x+noise, the true-signal candidate was selected and improved untouched test squared error by +0.43139. Thus a validation win is not *always* spurious.

## Capability
Built reusable selection_audit.py (CSV candidate_id, validation_loss, test_loss, baseline_validation_loss, baseline_test_loss): selects only by validation, reports both improvements and optimism gap, flags a validation winner that loses on untouched test. It explicitly cannot prove test data was truly untouched. Benchmark code: holdout_reuse.py. 16 unit tests passed locally. Seeds fixed, source and JSON output included in the local experiment bundle.

## Decision
Do not label a gold/SEO model 'better' based solely on repeated tuning against one holdout. Maintain an independent test set, record candidate search count and test provenance, and retire a test set once used adaptively for further development. Independent test success is not proof of future performance under drift.

## Limits
Synthetic IID data, deliberately inferior null candidates, no live market/SEO data, no model deployment, no evidence of a real bug in the existing gold site. 95% intervals quantify Monte Carlo uncertainty over simulated runs, not real-world predictive uncertainty.
