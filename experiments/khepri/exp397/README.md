# Khepri exp397 — selective-feedback audit and counterfactual policy evaluation

## Self-directed question
When an AI agent abstains on low-confidence cases, can it still measure its overall correctness and fairly evaluate a less conservative policy? Does random auditing of abstentions solve the feedback blind spot?

**Counterexample:** Accuracy on the *answered* subset is not accuracy across all opportunities. Gold-like simulation: selective accuracy 68.4%, but population correctness 46.0% at 33.8% coverage. SEO-like: 66.7% vs 44.2% at 21.8% coverage. Neither is a real-world forecast result.

## Tested capability
`selective_audit.py` implements (1) selective accuracy, (2) a Horvitz–Thompson inverse-probability-weighted estimator of full-population accuracy, and (3) an off-policy estimator of the mean reward of a different confidence threshold, using randomized audits of otherwise unobserved abstentions. If an unobserved stratum has **zero** probability of being labeled, the estimators fail closed rather than inventing an answer. A reward of +1 for correct, -2 for wrong, and -0.15 for abstaining is **illustrative**.

## Reproduce
Python 3.10+, standard library only:

```bash
python -m unittest discover -s experiments/khepri/exp397 -v
python experiments/khepri/exp397/benchmark.py --write
```

12/12 unit tests passed locally. Fixed RNG seed `3972026`. For each domain/scenario, 200 replicates × 3,000 opportunities = **600,000** simulated decisions, or **2.4 million** across two domains and two scenarios.

## Summary of synthetic evidence
| Domain | Audit mechanism | Selective accuracy | True full accuracy | Audit estimate of full accuracy | True alternative policy value | Audit estimate of value |
|---|---|---:|---:|---:|---:|---:|
| Gold-like | independent q=0.10 | 0.684 | 0.460 | 0.457 | -0.125 | -0.125 |
| SEO-like | independent q=0.10 | 0.667 | 0.442 | 0.440 | -0.134 | -0.137 |
| Gold-like | outcome-dependent (mislogged q) | 0.686 | 0.460 | 0.688 | -0.122 | +0.066 |
| SEO-like | outcome-dependent (mislogged q) | 0.668 | 0.441 | 0.735 | -0.132 | +0.021 |

Logging threshold = 0.75; alternative threshold = 0.65. In independent-audit runs, 95% normal-approximation confidence intervals over the 200 replicate-level **estimation biases** include zero for both domains and both estimators. In outcome-dependent runs, they do not. See `results.json` for values and intervals.

## Critical falsification
If audits depend on whether the prediction is actually correct (and the system *incorrectly records* a constant q=0.10), inverse-probability weighting becomes badly biased. The simulated adversarial selection audits 20% of correct abstentions but only 2.5% of incorrect abstentions. In this case, even the ostensibly audited estimator reports inflated accuracy and may reverse the sign of estimated policy value. Random auditing is useful **only if its sampling process and propensities are trustworthy**.

## Boundaries and design lessons
- These are *synthetic* confidence distributions and correctness outcomes, not real gold/SEO data or deployed agent telemetry.
- The estimators assume observed accepted decisions have labels, audited abstentions are selected independently of their unseen outcomes conditional on logged inclusion probabilities, and probabilities are accurate and strictly positive wherever needed.
- For delayed labels, do not treat not-yet-matured outcomes as false or as random missingness. Use only matured cohorts, or explicitly model censoring and its propensities.
- The full-accuracy Horvitz–Thompson estimate is unbiased under the assumptions but can lie outside [0,1] in finite samples. Never silently clip it when assessing bias.
- Counterfactual value estimates require a **predeclared reward function**, stable labels under the alternative decision policy, and no unmodeled action-dependent feedback. Do not optimize the alternative threshold and evaluate it on the same audited sample without holdout/correction.
- There is no claim of improved forecasting accuracy or deployable exactly-once behavior.

## Next useful experiment
Implement a real decision log with auditable randomization and label-maturity timestamps in a sandbox; compare IPS against a doubly robust estimator and test sensitivity to audit rate, reward misspecification, and nonstationary selection. No production integrations here.
