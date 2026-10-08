# Khepri experiment 80 — Markov expert-share e-process (2026-10-08)

## Goal
Experiment 79's 14-expert fixed switch grid had strong power at preselected change points, but poorer power for off-grid switches and stable signals. Test whether a capital-preserving, precommitted Markov expert-share portfolio covers arbitrary switch times with linear computational cost.

## Construction and proof
Two context specialists j=0,1. Each hazard h in {0.001,0.003,0.01,0.03} starts with capital (0.5,0.5). At time t, redistribute the two capital accounts via matrix [[1-h,h],[h,1-h]], **before observing X_t**; then multiply account j by (1+0.35*I(C_t=j)*X_t). Average the four hazard portfolios; also test a 50/50 blend with the static specialist portfolio.

If X_t in [-1,1], E[X_t | F_(t-1), C_t] <= 0, and C_t is observed before X_t, the factors are nonnegative with conditional expectations <=1. The Markov matrix conserves capital, so the sum of account capitals is a nonnegative supermartingale. Fixed convex mixtures retain the guarantee P(sup W_t>=20)<=0.05. **Marginal mean-zero alone is insufficient.** The recursion exactly sums exponentially many switch paths in O(KT) time; it is an application of established e-process methods, not a claim of a novel theorem.

## Paired synthetic benchmark
10,000 trajectories, 360 observations, lambda=0.35, threshold=20, independent seeds 8001 and 8017. All strategies see identical trajectories within each simulation. Static / exp79 grid / Markov hazard mix / hybrid crossing percentages, seed 8001:

| Scenario | Static | Grid | Markov | Hybrid |
| --- | ---: | ---: | ---: | ---: |
| Symmetric null | 4.09 | 4.13 | 4.06 | 4.02 |
| Dependent null | 2.73 | 3.67 | 3.01 | 2.81 |
| Switch t=60, mu=.25 | 58.34 | 61.70 | **68.74** | 65.74 |
| Switch t=180, mu=.25 | 59.02 | **72.62** | 69.29 | 66.47 |
| Switch t=300, mu=.25 | 72.69 | 67.16 | 73.06 | **73.51** |
| Stable, mu=.25 | 76.37 | 66.62 | 75.23 | **76.47** |
| Switch t=180, mu=.34 | 86.73 | **95.69** | 94.29 | 92.91 |

Seed 8017 confirmed the main effect: Markov minus grid +6.55 percentage points at switch t=60, -3.20 pp at t=180, +5.58 pp at t=300, +8.46 pp for stable mu=.25. Paired 95% Monte Carlo CI (seed 8001) for t=60: +6.41 to +7.67 pp; t=180: -3.89 to -2.77 pp. These CIs refer to simulation randomness, not real-world uncertainty.

## Independent validity checks and falsification
- 9 local unit tests passed, including explicit enumeration of 2^6 expert paths against the linear-time Markov recursion.
- Exact enumeration: 4^7 independent context/sign paths, and 2^8 weighted paths for a **dependent** conditional null where C_t=I(X_(t-1)>0). Every tested valid portfolio stays below its Ville bound.
- Additional null generators: symmetric +/-1, skew (+1 p=.2, -.25 otherwise), and dependent null with context-specific mean-zero outcomes. Simulated crossing rates stayed <5% for each of two seeds.
- **Counterexample:** the Markov mixture is NOT uniformly better. The fixed grid beats it by ~3.2–3.3 pp at its own switch point t=180. High switch hazard leaks capital under stable signals.

## Next step
Precommit a combined prior over grid and Markov paths using separate development scenarios, then evaluate on held-out scenarios. Do not optimize mixture weights on the same test results.

## Reproducibility and scope
Full executable code, 9 tests, and raw JSONL results generated locally as khepri_experiment80_bundle.zip. The code and data have **not** been uploaded to this branch by this report write. Authorized repository AUTONOMY_CHARTER.md was read directly from main. All experiments synthetic; no real-world deployment claim.
