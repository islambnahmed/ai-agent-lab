# Worker A cycle 238 — honest finite-population audit intervals under arbitrary nonresponse (2026-10-20)

## Problem and change of strategy
Cycle 237's exact hypergeometric intervals explicitly assumed **complete, accurate audit labels**. That assumption fails if selected audits do not respond, especially when failures are associated with the underlying error. Instead of optimizing the old interval's nominal width, this cycle adds a transparent partial-identification fallback and a tighter **Bonferroni hybrid**. The hybrid intersects (a) an exact direct binary-loss interval and (b) an exact proxy-residual interval; each is constructed at 97.5% confidence, so the intersection retains at least 95% design coverage. This is a simulation + mathematical construction, not a deployed model.

## Assumptions and derivation
- Fix a finite ledger of N items, binary true loss Y in {0,1}, and an observable, fixed binary proxy P. All P values are known for the full ledger.
- Select m rows uniformly without replacement **before** audit response occurs. Audit response can be arbitrary, including depending on Y, P, sample membership, or any other sampled data. If a label is returned, it must be accurate. m and the sampling design are fixed.
- For the direct interval, if k positive labels are observed and u labels are missing, the true number of positives in the *selected sample* lies between k and k+u. Invert both exact hypergeometric tails at alpha/4 for a 1-alpha/2 direct interval. The interval for any realized response pattern contains the full-data exact interval; the latter has at least 1-alpha/2 SRS design coverage.
- For the residual interval, define positive residual indicator A=1[Y=1,P=0] and negative residual indicator B=1[Y=0,P=1]. Their finite-population totals satisfy true risk = mean(P)+(total(A)-total(B))/N. For missing selected rows with P=0, A may be 0 or 1; with P=1, B may be 0 or 1. Invert one-sided hypergeometric tails at alpha/8 for the four residual tails to get a 1-alpha/2 interval. This interval likewise contains the complete-label interval pointwise for any response pattern.
- Intersect the two 1-alpha/2 intervals; by union bound the hybrid has >=1-alpha design coverage. **The guarantee is unconditional over the original SRS selection for a fixed ledger; it is not conditional on the selected sample, response count, or realized response pattern.** No MAR/MCAR assumption is made. The guarantee does not hold with inaccurate returned labels, non-SRS sampling, altered ledgers, adaptive reuse, or post-hoc tuning.

## Verification
- Node >=18, dependency-free `nonresponse-exact.mjs`.
- **540,272 assertions**: exhaustive hypergeometric count coverage for N=2..6, all K and m; for every binary proxy/true-loss ledger N=2..5, all possible samples and all possible withheld-label masks, the partial-label residual and hybrid intervals contain their respective full-label intervals; census edge cases.
- Two non-overlapping seeded evaluation sets of 200 trials each per response regime, N=400, m=60; synthetic 12% base error and a noisy proxy with shared-error modes.
- `naiveCoverage` is an intentionally misspecified complete-case normal approximation, not a comparable finite-population design interval.

| Regime | Trials | Missing (%) | Residual exact width (pp) | Hybrid width (pp) | Hybrid coverage (%) | Naive coverage (%) |
|---|---:|---:|---:|---:|---:|---:|
| Complete labels | 400 | 0.00 | 25.31 | **17.52** | 98.75 | 93.00 |
| MCAR ~30% | 400 | 30.14 | 56.78 | **49.01** | 100.00 | 91.25 |
| MNAR (missing mostly when Y=1) | 400 | 19.48 | 40.19 | **34.62** | 100.00 | **22.25** |
| Adversarial proxy-disagreement masking | 400 | 21.14 | 40.25 | **37.41** | 100.00 | 90.75 |

These summary rows average two independent seeded sets; exact per-set results are in `results.json`. High observed coverage (98.75–100%) does **not** prove 100% coverage or validate real-world performance. The width is still enormous when audits are missing. In the MNAR regime the naive complete-case CI covers truth only 20–24.5% of trials, illustrating how missing-not-at-random audits can create falsely confident estimates. The hybrid interval improves width over the residual-only exact method while retaining a design-based guarantee under stated assumptions.

## Limitations / negative result
No procedure can infer the unobserved audited labels without assumptions; when missingness is high, honest uncertainty remains wide. A confidence interval over a fixed ledger is not a model-generalization interval, and none of these results supports financial forecasting. Returned labels that are wrong are **not** addressed by this cycle. The current `logFactorials`/hypergeometric-tail implementation is intended for moderate N and should be numerically stress-tested before use at scale. The hybrid is deliberately conservative because it uses Bonferroni rather than a jointly inverted exact multinomial distribution.

## Recovery and next useful work
Run `node experiments/worker-a/nonresponse-exact.mjs` to reproduce all assertions and synthetic metrics. For a real evaluation, first verify sampling provenance and label accuracy; if either fails, report partial identification or halt certification rather than claiming nominal 95% coverage. Future work: tighter joint inversion with validated coverage, label-error bounds, and a decision rule that abstains when the audit interval crosses the deployment risk threshold. Do not merge into `main` without independent code review and CI.
