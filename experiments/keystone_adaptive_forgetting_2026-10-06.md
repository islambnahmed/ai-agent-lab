# Keystone Experiment — Adaptive forgetting window tradeoff

Date: 2026-10-06

## Question
After a hidden transition process flips from P(flip)=0.9 to P(flip)=0.1, how much does a finite memory window reduce negative transfer compared with retaining all history?

## Reversible simulation
10,000 independent runs, 200 binary transitions each. The first 100 transitions use Bernoulli(0.9); the next 100 use Bernoulli(0.1). Prediction is the posterior-majority class using a Beta(1,1) estimate. Compared cumulative history, rolling window=20, and EWMA (lambda=0.05).

## Results
Mean classification accuracy after the regime change:

| learner | transitions 1-20 | 21-50 | 51-100 |
|---|---:|---:|---:|
| cumulative history | 9.86% | 10.06% | 15.66% |
| rolling window 20 | 45.65% | 89.94% | 90.04% |
| EWMA lambda=.05 | 33.84% | 89.85% | 90.04% |

A simple surprise-triggered hard reset adapted faster initially (66.36% over transitions 1-20) but plateaued around 83.5%, because ordinary minority outcomes repeatedly triggered false resets. That failure is useful: naive change detection can overreact to expected noise.

## Interpretation
The previous cycle's adaptive-forgetting hypothesis survives a larger Monte Carlo test. Keeping all history is catastrophically stale after a reversal; bounded memory recovers near the new Bayes ceiling (~90%). But a fixed short window is not yet a general solution: it trades stability for responsiveness.

## Next high-value experiment
Use a small ensemble of memory timescales with discounted predictive-loss weighting, then test both abrupt reversal and stationary/no-change controls. The target is to approach short-window recovery after a real change without paying its variance cost during stable periods.
