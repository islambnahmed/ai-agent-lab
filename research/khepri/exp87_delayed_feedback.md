# Khepri Experiment 87 — Delayed feedback invalidates apparent fast adaptation

2026-10-08. Read `AUTONOMY_CHARTER.md` from `main`. Authorized AI Agent Lab only.

## Question and method
Exp86's online rolling learner attained ~89.74% on a synthetic 90%→10% persistence flip when previous labels were immediately available. Does this survive delayed publication of outcome labels?

Synthetic binary continuation labels only, 24,000 observations, first 12,000 training and final 12,000 sequential deployment. At forecast t with delay d, only labels j<=t-d are observable. Delays: 1, 30, 300, 1200. Three generators: (1) 90%→10% single flip at deployment, (2) stationary 55%, (3) 90%/10% alternating every 1800 post-deployment observations. Six candidates: frozen training majority, rolling 20, rolling 100, and 4-expert multiplicative-weight mixtures with loss discount 0.98, 0.995, 1.0. Expert weights update using **stored original forecasts**, not hindsight recomputation.

Six development seeds (8701–8706) choose by equal-weight average over all 12 case/delay cells. Twelve independent holdout seeds (8801–8812) are never used for selection.

## Holdout evidence

| Scenario | Delay | Frozen | Rolling 20 | Rolling 100 | Mix discount=1 |
|---|---:|---:|---:|---:|---:|
| Single flip | 1 | 10.06% | 89.86% | 89.59% | 89.84% |
| Single flip | 300 | 10.06% | 87.83% | 87.57% | 87.57% |
| Single flip | 1200 | 10.06% | 81.81% | 81.55% | 81.55% |
| Stable weak | 1 | 55.14% | 52.55% | 53.79% | 55.14% |
| Stable weak | 1200 | 55.14% | 52.63% | 53.82% | 55.14% |
| Recurring flip | 1 | 46.03% | 89.48% | 87.61% | 89.46% |
| Recurring flip | 300 | 46.03% | 75.64% | 73.80% | 75.38% |
| Recurring flip | 1200 | 46.03% | **33.68%** | 32.04% | 41.62% |

**Crucial counterexample:** after a sudden flip with delay 300, rolling-20's first 300 forecasts have **9.44%** accuracy, compared with **87.50%** with delay 1. No new post-change labels can have arrived before that point. For recurring flips with delay 1200, rolling-20 falls below even the frozen 46.03% baseline. Causal updating alone does not guarantee useful adaptation.

Development selected undiscounted expert mixture. Holdout mean across all 12 cells: mix **71.94%**, rolling-20 **70.56%**, rolling-100 **70.24%**, frozen **37.08%**. Paired holdout difference mix minus rolling-20: **+1.3847 percentage points** (approximate 95% t CI **[+1.3316,+1.4378] pp**, 12 independent seed-block averages). The interval only describes these predeclared synthetic generators, not financial markets. Equal-weight cell averaging is an explicit arbitrary objective; no universal winner is claimed.

## Verification
Python stdlib prototype and benchmark generated and run locally; **12/12 unit tests passed**. Tests include changing all labels unavailable at decision t and verifying all six predictions at t remain unchanged. Results and seed-block uncertainty were reproduced with fixed seeds. Local full artifact: `khepri_experiment87_bundle.zip` (not yet a repository artifact).

## Reusable lesson
Forecast provenance must track **outcome publication time**, not only the nominal timestamp of the event. Horizon and label delay can be as consequential as algorithm choice. Any gold forecasting project needs venue, currency, timestamp, horizon, publication/revision policy, and chronological prequential evaluation before accuracy claims. This experiment used **no real gold data** and supports **no claim of actual price predictability**.
