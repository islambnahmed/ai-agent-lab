# Khepri exp423 — Cluster-boundary anytime-valid evaluation

2026-10-24 · Authorized AI Agent Lab · synthetic local research only. No production or external service changes.

## Why this direction
After experiments 416–422 on local authorization/SQLite guards, revisit exp415's statistical limitation: a correct sequential e-process can make invalid decisions when repeated correlated events are treated as new independent/conditionally fair evidence.

## Method
For complete, predeclared cluster c, set Z_c = mean(X_c,1,...,X_c,m) where all X are in [-1,1]. The equal-cluster-weighted estimand differs from an event-weighted mean. If E[Z_c | earlier completed clusters] <= 0, each product over clusters of (1 + lambda Z_c), lambda in [0,1), is a nonnegative supermartingale. A fixed mixture is also a supermartingale. Ville's inequality bounds the probability of ever crossing 1/alpha by alpha. No independence within clusters is needed. This guarantee does NOT follow from marginal E[Z_c]=0 alone.

The deliberately naive comparator applies the same e-process after every event, including repeated events within the same cluster. Its assumption fails under cluster shocks. Decisions from the clustered process are available only after a full cluster; grouping and mixture must be predeclared.

## Reproduce
Python 3.10+ standard library only, run from this directory:

    python -m unittest -v test_cluster_evidence.py
    python benchmark.py

Local verification: 13/13 unit tests passed. Exact enumeration of all fair +/-1 cluster sign sequences through length 8 confirmed mean e-value 1 to floating-point precision. Benchmark: seed 423; 2,000 trials per scenario, 80 clusters/trial, alpha=.05, eight scenarios = 16,000 synthetic trials. Percentages are observed Monte Carlo threshold-crossing rates, not real-world error or prevalence estimates.

| Scenario | Event-level | Cluster-level |
| --- | ---: | ---: |
| SEO null, 8 identical events/cluster | 71.75% | 2.55% |
| SEO positive, P(+ cluster)=.62 | 97.65% | 35.15% |
| SEO null, singleton clusters | 2.10% | 2.10% |
| Finance null, noisy, variable cluster sizes | 50.65% | 1.75% |
| Finance positive, P(+ cluster)=.65, noisy | 95.50% | 47.50% |
| Counterexample: one global fair shock shared across all clusters | 50.85% | 50.85% |
| Counterexample: persistent regime, P(same sign next cluster)=.95 | 71.05% | 50.00% |
| Repair experiment: persistent regime plus independent randomized sign per cluster | 52.95% | 1.40% |

## Findings and limits
Within-cluster pseudoreplication can produce false positives despite a formally correct e-process. Predeclared cluster-level updates repair the conditional-null problem in the independent-cluster SEO and finance simulations, but lose apparent power versus the invalid comparator. They fail when a common regime persists across clusters. In the synthetic randomization repair, a fresh independent random sign per cluster restores conditional fairness even with a persistent background regime; this is a proof-of-concept experimental-design device, not a claim that any production intervention can be randomized this way.

Adaptive/outcome-dependent cluster size, retrospective grouping, selection among many candidate agents, nonrandomized persistent regimes, and use of partial clusters may invalidate the guarantee. No live SEO, financial, or LLM systems were tested. The previous exp415 e-process formula is not refuted: its conditional-null premise was violated by correlated observations.

**Reusable lesson:** The unit of sequential evidence must match the unit that supplies fresh conditional information. If dependence spans clusters, improve the experiment design rather than simply increasing the rejection threshold.
