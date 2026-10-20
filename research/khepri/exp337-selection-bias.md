# Khepri exp337 — Model-selection winner's curse

2026-10-21 | Authorized AI Agent Lab | **Synthetic, reversible experiment; production unchanged.**

## Question and methods
If an agent tries K forecast variants and reports only the best backtest, how often does a *completely non-predictive* candidate look significant? Simulated 6,000 trials per scenario with fixed seed 337, independent train/holdout standard-normal z-scores, one-sided alpha=0.05. Compared (a) naive significance of best training candidate, (b) Bonferroni alpha/K, and (c) significance on one untouched holdout. Tested K=1,10,50,100; correlated candidates rho=0.9; a strong real synthetic edge, then the same edge disappearing at holdout. Transferred to 50 independent SEO campaigns with 100 Bernoulli trials per campaign, known baseline conversion probability 0.1 and exact binomial tails. This SEO setting is *not* a shared-control A/B test.

## Measured results (6,000 Monte Carlo trials/scenario)
| Case | K | Naive train significant | Bonferroni train significant | Selected holdout significant |
| --- | ---: | ---: | ---: | ---: |
| Gaussian null | 1 | 4.90% | 4.90% | 4.80% |
| Gaussian null | 10 | 41.18% | 4.55% | 4.65% |
| Gaussian null | 50 | **92.35%** | **4.37%** | **5.15%** |
| Gaussian null | 100 | **99.25%** | 4.98% | 5.02% |
| Gaussian null, rho=0.9 | 50 | 16.88% | 0.70% | 5.02% |
| SEO exact-binomial null | 50 | **87.10%** | 3.85% | 4.10% |
| One stationary real edge | 50 | 99.92% | 82.00% | 93.37% |
| Same edge disappears at holdout | 50 | 99.95% | 82.30% | **4.42%** |

**Analytic check:** under independent exact-null p-values, familywise false-positive probability = 1 - 0.95^K; for K=50, 92.3055%. The measured 92.35% matches. Independent stdlib implementation independently reproduced the K=50 null as 92.45% naive, 4.68% Bonferroni, 5.33% holdout. SEO replication: 86.82%, 3.98%, 4.28%. 12 extended unit tests and 7 stdlib self-checks passed. Approximate 95% Monte Carlo halfwidth near a 5% rate: 0.55 percentage points.

## Counterexamples and transferable lesson
- Picking the most impressive of 50 backtests and treating its p<0.05 as confirmatory is invalid: 92% false discoveries under the independent null.
- Highly correlated candidates reduce effective multiplicity; Bonferroni controls false positives but can be conservative.
- A clean holdout is not a promise of stability: if an actual effect disappears at deployment, the selected candidate fails out of sample.
- Exact binomial inference does not by itself fix SEO variant selection bias.

## Proposed read-only integration
Record **all** candidate variants and their selection criteria, correct for selection multiplicity, freeze the selected model, then evaluate it **once** on an untouched forward-time holdout with true data-availability timestamps. For financial series, account for autocorrelation, volatility regimes, and purging/embargo as applicable. Reusing the holdout invalidates its confirmatory status.

## Limitations
Synthetic controlled experiment only: **no verified claim about actual gold forecast quality or production defects**. Gaussian test assumes known variance and independent scores; actual market data may be heavy-tailed, serially dependent, or nonstationary. SEO example assumes independent campaigns and a known baseline, not a shared-control experiment. Bonferroni does not repair temporal leakage, repeated holdout peeking, or regime drift. The strong positive control is intentionally not a realistic claimed trading edge.

## Reproduction
Full tested scripts: `selection_bias_benchmark.py` (NumPy/SciPy) and `selection_bias_core.py` (stdlib replication), plus JSON outputs in the local exp337 reproducibility bundle. The core independent implementation can be published on this research branch.

**Decision:** no production change. Prioritize audit of the actual model selection protocol and trial counts, not another synthetic optimization tweak.
