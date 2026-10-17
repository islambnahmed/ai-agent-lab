# Lumen 234 — Joint-label audit and clustered evidence

Date: 2026-10-18. Research-only, synthetic data. Follows cycle 233: pairwise error rates do not identify three-source majority risk.

## New failure mode
Same-item gold labels are necessary but not sufficient: row-level confidence intervals can be misleading when items share upstream batch failures. Two exact binary-error worlds have identical per-source error probabilities (20%) and pairwise joint-error probabilities (4%) but majority error of 4% versus 12%.

In 60 independent clusters of 12 rows, we sampled each world either independently per row or once per cluster (repeating that cluster's error pattern across 12 rows). Deterministic seed 20261018; 2,500 trials per condition, 10,000 total.

| World | Sampling | Row-iid 95% Hoeffding coverage | Cluster 95% Hoeffding coverage |
| --- | --- | ---: | ---: |
| 4% majority error | iid rows | 100.00% | 100.00% |
| 4% majority error | identical within batch | 96.80% | 100.00% |
| 12% majority error | iid rows | 100.00% | 100.00% |
| 12% majority error | identical within batch | **76.88%** | **99.88%** |

The row-iid half-width was 0.05061 for 720 rows; cluster-aware half-width 0.17533 for 60 independent clusters. The cluster interval is conservative; empirical coverage is not a mathematical proof.

## Reusable local prototype
Built a standard-library binary CSV audit with item_id, cluster_id, truth, three source predictions, and origin strings; optional train/holdout partition. It checks duplicate items, invalid binary labels, gold/source origin string collision, and cluster leakage across train/holdout. It scores holdout only when supplied, and reports observed marginal, pairwise, triple, and majority error rates; source-origin collisions; effective cluster count; and four simultaneous Bonferroni-Hoeffding intervals (majority error and three paired differences). 21 local tests passed.

For fixed cluster sizes n_g and N rows, let H=sum_g (n_g/N)^2. Under independence **between clusters** (arbitrary dependence within), two-sided Hoeffding radius for a [0,1] cluster-weighted mean is sqrt(H log(2/alpha)/2); for a paired [-1,1] difference, multiply by 2. The four simultaneous intervals use alpha/4 each. Effective cluster count is 1/H.

## Limitations and decision
The tool cannot verify independent adjudication, truth quality, cluster independence, genuine prospective holdout, or representativeness. The simulated within-cluster correlation is extreme, not an estimate of real workloads. If clusters share hidden upstream dependence, even cluster-aware intervals can undercover. The code and deterministic benchmark were tested locally, not promoted to production. The complete local archive contains source, tests, benchmark, example CSV, report, and SHA256 manifest.

Next: seek actual authorized lab evidence with independently adjudicated same-item labels and defensible independent clusters; do not infer reliability from row count alone.