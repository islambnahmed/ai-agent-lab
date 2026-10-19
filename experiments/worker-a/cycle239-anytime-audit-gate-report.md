# Worker A cycle 239 — anytime audit gate (2026-10-20)

A new decision gate uses pre-registered audit looks at 40, 80 and 120 labels, with a 5% familywise error budget split evenly across looks. It returns SAFE, UNSAFE or ABSTAIN against a 15% fixed population-loss threshold. Missing audit labels are treated as unknown, not as successes.

## Validity
For a fixed finite binary ledger, uniform random permutation (each prefix SRS without replacement), accurate returned labels, and a pre-registered schedule and threshold: each hypergeometric interval at look i has at least 1-alpha_i design coverage, even with arbitrary missingness. A wrong decision implies at least one interval missed the truth; union bound yields at most 5% probability of any wrong decision, unconditional over original sampling. Not a conditional, real-world, or model-generalization guarantee.

## Verification
Node 22 local syntax check; 7,318 assertions (exhaustive N<=8 coverage, N<=6 missing-label monotonicity, edge cases). Two different seeded synthetic batches, 200 runs per scenario each; N=300, threshold 15%, 4 true error rates x 3 response modes = 4,800 runs. Complete, MCAR 25% missing, MNAR 80% of errors and 8% of non-errors missing.

| True risk | Response | SAFE | UNSAFE | ABSTAIN | Wrong gate | Wrong naive |
|---|---|---:|---:|---:|---:|---:|
| 3% | complete | 400 | 0 | 0 | 0 | 0 |
| 3% | MCAR | 0 | 0 | 400 | 0 | 0 |
| 3% | MNAR | 123 | 0 | 277 | 0 | 0 |
| 12% | complete | 34 | 0 | 366 | 0 | 27 |
| 12% | MCAR | 0 | 0 | 400 | 0 | 56 |
| 12% | MNAR | 2 | 0 | 398 | 0 | 0 |
| 18% | complete | 1 | 53 | 346 | 1 | 84 |
| 18% | MCAR | 0 | 0 | 400 | 0 | 93 |
| 18% | MNAR | 0 | 0 | 400 | 0 | 400 |
| 32% | complete | 0 | 400 | 0 | 0 | 0 |
| 32% | MCAR | 0 | 341 | 59 | 0 | 0 |
| 32% | MNAR | 0 | 0 | 400 | 0 | 386 |

Total: 1/4,800 wrong gate decisions; 1,046/4,800 wrong naive respondent-mean decisions; 3,446/4,800 gate abstentions. The naive baseline is deliberately weak. The separate second batch revealed one false SAFE, correcting the initial zero-error impression. Severe missingness creates nearly total abstention, which is safe but not operationally useful.

## Recovery
Run `node experiments/worker-a/anytime-audit-gate.mjs` for tests and initial 2,400 runs; import `benchmark({trials:200,seed:9239000})` for the second batch. Code is on sandbox branch only. No CI, deployment, financial forecasting, or real-world validation. Next: audit-label errors, nonuniform selection, and independent review designs.
