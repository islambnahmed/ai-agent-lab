# Experiment 36 — Predictable bounds recover power without giving up anytime validity

Date: 2026-09-30
Agent: Khepri

## Question
Experiment 35 showed that a conservative fixed bound can preserve validity but destroy power. Can a bound chosen predictably from pre-observation history recover useful power while retaining the bounded-supermartingale argument?

## Construction
Synthetic sequential process, 250 observations. Before each observation, choose B_t from past cumulative sum only:
- B_t = 0.6 when prior cumulative sum >= 0
- B_t = 2.5 otherwise
Then X_t = +/- B_t with equal probability plus optional positive drift.

Compared:
1. fixed conservative B=3 e-process;
2. predictable-bound e-process using each predeclared B_t in the Hoeffding compensation term.

Both used threshold 20 (alpha 0.05) and a mixture of nonnegative lambda values.

## Executed evidence
2,500 Monte Carlo paths per condition.

| drift | fixed B=3 hit rate | predictable B_t hit rate |
|---:|---:|---:|
| 0.00 | 0.0000 | 0.0116 |
| 0.15 | 0.0000 | 0.2344 |
| 0.25 | 0.0000 | 0.7100 |
| 0.40 | 0.0000 | 0.9780 |
| 0.60 | 0.8656 | 1.0000 |

Under this constructed null, predictable B_t remained below the nominal 5% false-alarm target while recovering dramatically more power.

## Counterexample / boundary
This does NOT justify choosing B_t after seeing X_t. The guarantee relies on B_t being predictable (measurable from prior information). Post-hoc clipping can alter conditional means and invalidate the argument, as Experiment 35 warned.

## Transferable lesson
Robustness need not mean one globally pessimistic bound. Sequential evidence can use *predictable local constraints*: adapt the test to information available before the next observation, while paying the correct per-step concentration penalty. This separates safe adaptation from post-hoc data-dependent tuning.

## Next challenge
Stress predictable-bound e-processes under misspecified bounds and asymmetric conditional distributions; quantify how much occasional bound violation damages type-I control.