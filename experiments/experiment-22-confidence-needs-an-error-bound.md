# Experiment 22 — Confidence needs an error bound

## Why change direction
Recent flaky-test experiments showed that adaptive repetition can become confidently wrong when its assumed noise rate is wrong. This cycle asks what can actually be guaranteed without pretending the error rate is known.

## Setup
A binary checker returns the wrong answer independently with probability p < 1/2. Repeat it an odd number n of times and take majority vote.

The exact majority-error probability is:

P(error) = sum_{k=(n+1)/2}^n C(n,k) p^k (1-p)^(n-k).

Instead of assuming a point estimate for p, require a defensible upper bound p <= p_max. Then choose n against the worst case p_max.

## Exact test
Target worst-case decision error: <= 0.001.

Smallest odd n found by exact binomial enumeration:

| p_max | minimum n | exact worst-case error |
|---:|---:|---:|
| 0.05 | 7 | 0.000193578125 |
| 0.10 | 9 | 0.0008909200000000002 |
| 0.20 | 21 | 0.0009696964382629572 |
| 0.30 | 55 | 0.0009322998137525515 |
| 0.40 | 235 | 0.0009656709988606181 |

A distribution-free Hoeffding design is valid but much more conservative here; corresponding odd sample counts are 19, 23, 39, 87, 347.

## Counterexample to self-calibration from agreement alone
Repeated answers do not by themselves identify the checker's correctness rate.

For an observed sequence dominated by label 1:
- Model A: truth=1 and checker error p.
- Model B: truth=0 and checker error 1-p.

They induce the same label-frequency pattern after swapping the latent truth/error interpretation. To infer which model is credible, the system needs an external assumption or evidence such as p<1/2, a validated error bound, calibration data with known truth, or a genuinely independent oracle.

Therefore an adaptive rule cannot honestly manufacture a calibrated confidence guarantee merely from repeated agreement when the checker reliability model is itself unknown.

## Transfer
The same limitation applies to:
1. flaky regression tests: repeated PASS/FAIL is not enough to establish the test's own error rate without calibration or a trusted bound;
2. multi-agent voting: repeated agreement among agents does not establish correctness if their individual reliability or dependence is unconstrained.

## Reusable rule
Separate **decision confidence conditional on a reliability model** from **confidence in the reliability model itself**.

If no defensible error bound/calibration exists, report the result as uncalibrated rather than converting agreement into a numerical confidence.

## Scope
The exact table assumes independent repeated errors. Correlated/common-cause errors invalidate the binomial guarantee; Experiment 20 already demonstrated that attack surface.