# Worker A — Cycle 133: causal volatility proxy failure modes (2026-10-15)

**Research-only; entirely synthetic. No gold prices or production model were used.**

## Question
Cycle 132 showed improved early interval coverage when an *idealized* observable proxy and target volatility both jumped. Does the effect survive a lag, proxy/target decoupling, or a false alarm?

## Setup
100 seeded replications per case, 720 issues each; AR(1) shocks with rho=0 or 0.6. Target forecast errors use future shocks at t+1..t+h; h=7 or 30. Only residuals from issues i with i+h<t can enter the 80-label calibration window. Proxy at issue t is trailing RMS of 20 signals observable at t (or t-10 in the delayed case). Nominal interval coverage is 80%. Regime change starts at issue 400. Early phase: issues 400–479; late phase: 550–679. Baseline = rolling absolute-error quantile; alternative = quantile of mature error/proxy multiplied by current proxy.

| Synthetic scenario (rho=0) | h | Early rolling coverage | Early proxy coverage | Proxy/rolling width ratio | Late proxy coverage |
|---|---:|---:|---:|---:|---:|
| Target+proxy both jump 3x | 7 | 59.0% | 82.1% | 1.70x | 80.0% |
| Target jumps; proxy delayed 10 observations | 7 | 59.0% | 80.0% | 1.82x | 79.8% |
| Target jumps; independent proxy stationary | 7 | 59.0% | 59.2% | 1.03x | 79.5% |
| Proxy jumps; target stationary (false alarm) | 7 | 80.7% | 96.7% | 2.18x | 79.5% |
| Target+proxy both jump 3x | 30 | 54.2% | 84.0% | 2.38x | 76.5% |
| Target jumps; proxy delayed 10 observations | 30 | 54.2% | 79.8% | 2.44x | 76.4% |
| Target jumps; independent proxy stationary | 30 | 54.2% | 54.2% | 1.03x | 75.7% |
| Proxy jumps; target stationary (false alarm) | 30 | 77.9% | 96.4% | 2.63x | 75.7% |

## Findings
1. **Causal does not imply informative.** If proxy volatility stays flat while target volatility triples, the early coverage gain disappears (h30: 54.2% vs 54.2% rolling).
2. **False alarms are expensive.** If only proxy volatility rises, nominally excellent coverage is purchased with 2.18x–2.63x interval width. Report width and coverage together.
3. **Ten-observation lag did not erase the gain in this specific synthetic setup.** It increases widths and slightly reduces coverage. Avoid an overbroad claim that all proxy delay is fatal.
4. **The h30 late phase remains under target.** Observed 75–77% late coverage warns against treating short-horizon results as a calibration guarantee.

## Verification and limitations
Local reference experiment: `proxy_failure_modes.py --test` passed **10 tests** (causal observations, label maturity, reproducibility, invalid inputs); `--reps 100` generated numerical results and standard errors for rho=0 and rho=0.6. The repository file is a compact equivalent implementation; its content was read back from GitHub, but the exact published version was **not** run in GitHub CI during this cycle. Numerical table was generated from the locally tested reference version. No claim of real-market predictive improvement.

**Action:** Before any real gold integration, use timestamped proxy observations available at issue time, evaluate genuinely forward-issued forecasts, audit proxy/target coupling and false alarms, and require both conditional coverage and reasonable width against a rolling baseline. Do not tune an acceptance gate on the evaluation holdout.

**Source:** `experiments/worker_a/proxy_failure_modes.py` in this branch; full local JSON and reference script retained in the cycle artifact.
