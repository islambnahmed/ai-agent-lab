# Khepri exp443 — offline policy evaluation under selective feedback

Date: 2026-10-25. Python standard-library simulation; no external API calls, trades, SEO changes, or production data.

## Direction change

Exp437–442 focused on execution safety. This experiment instead tests a transferable evaluation capability: estimating a new AI agent policy from outcomes logged by a different policy, without pretending that missing counterfactual outcomes were observed.

## Hypotheses

**H0:** mean reward of logged examples whose actions match the new policy estimates that policy's value.

**H1:** context-dependent logging propensities distort that subset. Inverse propensity scoring (IPS), self-normalized IPS (SNIPS), and two-fold cross-fitted doubly robust (DR) estimators reduce bias when logging probabilities are correct and the target has overlap.

## Setup

Two contexts and two actions. Contexts are equiprobable; logging selects action 1 with probability 0.9. The proposed target action depends on context.

- **SEO:** binary simulated success; target outcomes are 0.75 in context 0 and 0.25 in context 1. True target value 0.5.
- **Gold:** continuous simulated reward with Gaussian standard deviation 1.5; target means +1.2 and -0.2. True target value 0.5 reward units. Not a trading strategy.

Each domain uses 300 deterministic repetitions of 600 logged decisions, totaling **180,000 synthetic decisions per domain**. The benchmark evaluates naive matched-action mean, IPS, SNIPS, and DR; DR fits context/action outcome means using the other half of the logged data with simple smoothing. The true policy value is available to the evaluator from the generator, but not to the estimators.

## Verified simulation results

| Domain | True | Naive mean / bias | IPS mean / bias | DR mean / bias | IPS RMSE | DR RMSE | ESS / 600 |
|---|---:|---:|---:|---:|---:|---:|---:|
| SEO | 0.5000 | 0.7000 / +0.2000 | 0.5015 / +0.0015 | 0.4999 / -0.0001 | 0.0489 | 0.0421 | 108.69 |
| Gold | 0.5000 | -0.0698 / -0.5698 | 0.4794 / -0.0206 | 0.4852 / -0.0148 | 0.1845 | 0.1537 | 108.39 |

SNIPS results are in `benchmark_results.json`. DR performs best in these particular simulations, not universally.

## Deliberate counterexamples

1. **Wrong propensities:** substituting 0.5 for the actual 0.9 logging probability makes the SEO IPS estimate inaccurate by about 0.196 in a 100,000-row fixed-seed test.
2. **No overlap:** when logging always chooses action 1, the target's action 0 in context 1 has no data. The support guard rejects estimation, even with 10,000 logged rows.
3. **Near-zero overlap:** changing logging probability to 0.99 worsens IPS variance and effective sample size relative to a balanced 0.5 logging policy.

## Reproduction

From this folder with Python 3.10+:

```bash
python -m unittest -v test_ope
python benchmark.py
```

Twelve tests passed locally. The benchmark deterministically rewrites `benchmark_results.json`.

## Limits and reusable lesson

The simulation assumes stationary contexts, correctly recorded propensities, no hidden confounding, no delayed feedback, and no action interference. It has only two contexts and two actions. It does **not** validate a real SEO or gold agent, nor justify production deployment. Confidence intervals, propensity audits, drift tests, and controlled exploration would be required.

**Lesson:** a policy may appear better because historical agreement selects favorable contexts. Propensity-aware evaluation plus overlap diagnostics is essential; a corrected point estimate without support and uncertainty diagnostics is insufficient.
