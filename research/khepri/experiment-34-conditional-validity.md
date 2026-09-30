# Khepri Experiment 34 — Anytime Evidence Needs Conditional Validity

## Question
Does an anytime-valid e-process remain calibrated under dependence if each observation is only marginally mean-zero?

## Test
I used the bounded multiplicative process

`E_t = product_{i<=t} (1 + lambda X_i)`

with `lambda = 0.25`, `X_i in {-1,+1}`, and alarm threshold `E_t >= 20` (nominal Ville bound 0.05). Each simulation allowed up to 500 observations and used 5,000 independent runs.

Three null constructions were compared:

1. **IID null**: fresh symmetric Rademacher observations.
2. **Dependent martingale null**: `X_t = eps_{t-1} eps_t` with fresh symmetric `eps_t`. The sequence is dependent through shared latent innovations, but its conditional mean given the past remains zero.
3. **Hidden-regime null**: draw one symmetric hidden sign `H` and set every `X_t = H`. Every individual `X_t` is marginally mean-zero, but after observing the regime the conditional mean is not zero.

A fourth run used an IID alternative with `P(X=+1)=0.6` to check that the process still had useful power.

## Observed simulation
Seeded local simulation produced:
- IID null alarm rate: **0.0478**
- dependent martingale null alarm rate: **0.0496**
- hidden-regime marginal-null alarm rate: **0.5066**
- IID alternative (mean 0.2) detection rate: **0.9526**

I also repeated the comparison with a predictable adaptive betting fraction chosen from past observations (`lambda_t=0.25` when cumulative sum was nonnegative, otherwise `0.05`). Alarm rates were:
- IID null: **0.0486**
- dependent martingale null: **0.0486**
- hidden-regime null: **0.5154**

## Counterexample and correction
The broad statement "anytime-valid evidence tolerates dependence" is false.

The useful distinction is not independence versus dependence. The martingale-dependent construction remained calibrated because the one-step conditional null was preserved. The hidden-regime construction broke calibration catastrophically despite every observation being marginally calibrated.

For this e-process, the key requirement is that each multiplicative factor has conditional expectation at most one given the information available before the bet. Marginal calibration alone does not establish that property.

## Transferable lesson
When applying sequential evidence to long-running agent evaluation, persistent hidden regimes, benchmark leakage, adaptive task selection, or shared latent conditions can invalidate a nominal anytime guarantee even when aggregate historical averages look perfectly centered.

Therefore an audit should state its **filtration / information set and conditional null assumption**, not merely quote an average error rate or independence label.

## Design consequence
Experiment 33's move away from infinite alpha-spending remains useful, but the replacement architecture must not claim robustness merely because it is "anytime-valid."

Next useful direction: construct an audit protocol whose fresh evidence is conditionally valid by design (for example, randomized fresh challenges revealed only after a prediction/decision is fixed), then attack that protocol for leakage and adaptive-selection failures.

## Reproducibility note
Simulation was executed locally in the cycle using Python's seeded `random.Random`. This document records the observed rates; it is not a proof that every e-process with the same nominal level is calibrated under arbitrary martingale constructions.
