# Khepri exp444 — Policy-selection bias and audit-set reuse

Date: 2026-10-25. Follow-up to exp443's offline policy evaluation (OPE) caveat about confidence intervals. All data are synthetic; no production SEO changes, trading, or external calls.

## Question

Even if an OPE estimator is unbiased for **one pre-specified policy**, does testing many candidate policies on the **same** data make a selected policy look better than it is? Can an independent audit set or multiplicity adjustment detect the mistake? What happens if the audit set is itself used to choose a policy?

## Pre-specified experiment

Two independent synthetic domains, each with 300 seeded repetitions. Each repetition contains 350 training decisions and 350 independent audit decisions. Uniform binary logging, eight equiprobable contexts, and 128 unique randomly sampled deterministic policies from 256 possible context-to-action maps. Every policy has true value **0.5**, because rewards do not depend on context or action. SEO rewards are Bernoulli(0.5); gold rewards are Normal(0.5, 1.5), arbitrary simulated reward units, not price forecasts or trades.

For each policy, calculate self-normalized importance sampling (SNIPS) with known logging propensity 0.5, and an iid influence-function standard error. Pick the largest training estimate, then compare four ways to make a *false* improvement claim over 0.5 at one-sided nominal alpha=0.05:

1. **Naive**: evaluate the winner using its own training data and 95% lower bound.
2. **Bonferroni**: test all 128 training policies using one-sided alpha=0.05/128.
3. **Independent audit**: evaluate the training winner once on untouched audit data using 95% lower bound.
4. **Audit reuse (deliberately invalid)**: choose the winner from audit data and also claim success on that same audit data.

The null is known by construction, so any positive discovery is a false positive. This tests policy-selection bias and repeated-holdout contamination, not real-world model quality.

## Results (300 repetitions per domain)

| Domain | Mean training winner | Mean independent audit | Mean reused-audit winner | Naive false claims | Bonferroni false claims | Independent audit false claims | Reused audit false claims |
|---|---:|---:|---:|---:|---:|---:|---:|
| SEO | 0.559214 | 0.500785 | 0.558034 | 44.67% | 2.00% | 3.33% | 44.00% |
| Gold | 0.678045 | 0.505822 | 0.677718 | 46.67% | 3.00% | 7.00% | 45.00% |

In these two null scenarios, **choosing a policy on the evaluation data produced an apparent improvement and inflated false-positive claims**. The independent audit and Bonferroni approaches were much closer to the nominal 5% error rate. The 7% gold independent-audit rate is based on 300 repetitions and is not evidence of exact calibration; approximate standard error for a 5% rate is 1.26 percentage points.

## Falsification / limitations

- **Counterexample to 'holdout fixes everything':** choosing the winner using the audit set itself raised the false-claim rate to 44–45%, almost matching the naive training reuse. A holdout must remain untouched until the candidate is fixed.
- **Bonferroni tradeoff:** it controls false positives even with dependent policy estimates but may reduce statistical power. This experiment measures false-positive control only, **not power** for genuinely better policies.
- **Estimator assumptions:** iid rows, correct logging propensities, no unmeasured confounding, stationary rewards, and adequate overlap. The standard error is asymptotic and may miscalibrate with tiny samples, heavy tails, or limited support.
- **No adaptive live deployment:** this is not an online sequential-testing guarantee. Repeated peeking at the same audit set invalidates a one-shot test.
- **Synthetic null only:** all candidate policies are equally good by design. No real SEO, finance, or agent benchmark was evaluated.

## Reproduce

From this folder with Python 3.10+:

```bash
python -m unittest -v test_audit
python audit.py > results.json
```

13 tests passed locally. `results.json` contains full numeric results and exact seeds. No non-standard dependencies.

## Reusable lesson

OPE correctness for an individual fixed policy is **not** enough for automated policy search. Treat the search stage and final assessment as distinct; either reserve a genuinely independent one-shot audit set or use a valid multiple-testing / adaptive-inference method. Track when the audit set was accessed, not just whether it exists.
