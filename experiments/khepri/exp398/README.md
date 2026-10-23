# Khepri exp398 — Policy-search optimism under sparse selective feedback

## Question
Exp397 showed randomized audits can estimate the value of a **fixed** confidence threshold. Does searching multiple thresholds and reporting the maximum in-sample estimate remain valid? Does an independent holdout fix this, including under deployment drift?

## Reproduce
Python 3.10+, standard library only:

```bash
python -m unittest discover -s experiments/khepri/exp398 -v
python experiments/khepri/exp398/benchmark.py --write
```

16/16 tests passed locally. Seed 3982026. Eight scenarios: gold-like and SEO-like × 2%/10% randomized audits × no shift / -0.20 correctness shift. Each scenario has 100 replicates with 900 train + 900 holdout + 900 deployment cases, **2,160,000 synthetic opportunities** total. Candidate thresholds .35–.95, 13 values. Rewards: +1 correct, -2 wrong, -0.15 abstain.

## Key results (mean reward units per opportunity)
| Domain | Audit q | In-sample selection optimism, no shift | Holdout error, no shift | Holdout overstatement after drift |
|---|---:|---:|---:|---:|
| Gold-like | 2% | +0.08269 | -0.01918 | +0.25346 |
| Gold-like | 10% | +0.02638 | -0.00145 | +0.21675 |
| SEO-like | 2% | +0.11816 | -0.00201 | +0.19496 |
| SEO-like | 10% | +0.03157 | +0.00083 | +0.15487 |

95% replicate-level intervals for q=2% optimism exclude zero: gold [+0.05935,+0.10602], SEO [+0.09281,+0.14351]. Holdout-error intervals in no-shift cases include zero. Under shift, holdout-vs-deployment gap intervals exclude zero: gold [+0.22496,+0.28195], SEO [+0.15558,+0.23433]. All scenarios are in results.json.

## Counterexample and boundaries
A Horvitz–Thompson estimator for a **fixed** threshold is unbiased under honest randomized audits, but selecting the maximum of 13 noisy estimates and then reporting that same maximum introduces a winner's curse. Independent holdout evaluation removes selection-induced optimism in stationary cases; it does **not** solve drift between validation and deployment. A 1.96×standard-error search penalty is a heuristic, not a valid post-selection confidence guarantee.

The experiments are synthetic; no real gold/SEO performance is asserted. The estimator requires correct strictly positive propensities for counterfactual accepted cases, mature labels for logged accepted decisions, independent audit inclusion conditional on observed features, fixed rewards, and action-invariant correctness. Holdout reuse for repeated tuning destroys independence. Report policy coverage alongside reward before considering deployment.
