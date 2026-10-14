# Khepri exp173 — overlap stress-test and proper interval score (2026-10-14)

**Scope:** Research-only, synthetic, no live XAU/USD data or production changes. Cross-review of Khepri exp172.

## Question
Exp172 reported a +3.96 percentage-point coverage gain for an 80%-target volatility-proxy band at horizon 30 in alternating synthetic regimes. But its per-origin absolute forecast errors were sampled independently. Actual 30-close persistence forecast errors share future returns across overlapping windows. Does the coverage improvement survive overlap and remain worthwhile after penalizing interval width?

## Reproducible design
Generate a seeded path of log returns with low/high volatility regimes (40-close alternating, 120-close alternating, permanent shock, stationary), optional AR(1) return correlation (rho=0 or 0.5). At origin i, the no-change forecast has absolute relative error `abs(expm1(sum(logreturns[i:i+h])))`. Score j is available only at origin >=j+h. Compare the exp172 unchanged rolling matured-error quantile against its past-return-volatility normalized quantile, using h=1,7,30, 100-error rolling window, 10-return proxy lookback, 80% target, and forecast origins 600..1199. 40 independent seeds per scenario/horizon/rho = 960 simulated paths, 576,000 **overlapping, non-independent** scored origins.

Proper symmetric 80% interval score: `2*halfwidth + 10*max(0,abs_error-halfwidth)`; smaller is better. Do not judge only by coverage.

## Findings (40-seed means, rho=0)
| Case | Rolling coverage | Proxy coverage | Rolling half-width | Proxy half-width | Rolling score | Proxy score |
|---|---:|---:|---:|---:|---:|---:|
| Stationary h30 | 77.07% | 77.73% | 4.22% | 4.49% | 12.22 | 12.79 |
| Alternating 40 h30 | 77.65% | 78.89% | 12.28% | **21.94%** | 38.37 | **57.43 (worse)** |
| Alternating 120 h7 | 73.09% | 80.44% | 5.37% | 6.68% | 20.57 | **17.72 (better)** |
| Alternating 120 h30 | 69.98% | 79.10% | 11.04% | 18.23% | 45.04 | **46.78 (worse)** |

The 40-close h30 case falsifies coverage-only promotion: +1.25pp coverage costs +9.66pp mean half-width and **+19.06** worse interval-score units. h7 in slower 120-close regimes transfers positively: +7.35pp coverage and -2.85 better score. Overlap matters: stationary h30 score lag-1 autocorrelation ~0.91; the seed-to-seed coverage standard deviation is 1.51x the naive n=600 binomial SD. Do not treat the 600 overlapping origins as independent.

## Verification and decision
Ten local Node tests passed, including future-score and future-return perturbations that leave previously issued bands unchanged. The complete reproducible scripts, benchmark output, and tests were generated locally as `khepri_exp173_reproducible.zip` (SHA-256 `30e3eeea0989f17a8554fe388d4e589e17355e05ebf0428463b676006ac2663e`). **The ZIP is not in this repository unless separately uploaded.**

**Decision:** Do not promote the exp172 proxy on coverage alone. For future real gold receipts require maturity embargo, overlapping-target-aware evaluation, coverage+width+proper interval score, and independent historical blocks or genuinely prospective receipts. Results are only from synthetic paths and do not establish real gold forecast skill. No production model was modified.
