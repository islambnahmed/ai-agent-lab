# Gold Lab synthetic regime challenge — Keystone, 2026-10-24

## Why this experiment exists

Gold Lab has invested heavily in source and receipt integrity. That is necessary but **not evidence of predictive skill**. This small independent experiment asks a different, falsifiable question: *when model selection favors a predictor in one period, how often does that advantage survive a clean later period under known synthetic dynamics?*

The executable imports the **actual four predictors** from `products/gold-forecast/models.mjs` (persistence, damped momentum, mean reversion, Ridge). It does **not** import or reproduce the entire production `forecast.mjs` selection/calibration/audit workflow. It neither changes production defaults nor touches any market data or frozen receipts.

## Run

From repository root, Node >=22, no downloads or external dependencies:

```bash
node --test experiments/keystone/gold_regime_stress.test.mjs
node experiments/keystone/gold_regime_stress.mjs --seeds=64
node experiments/keystone/gold_regime_stress.mjs --seeds=64 --json
```

The 64-path run is deterministic for the same model source. It takes roughly 8 seconds on the local Node 22 test machine; runtime is hardware-dependent. The `--json` output is machine-readable but intentionally not committed as a frozen production benchmark. This is a *diagnostic challenge*, not a tuned trading strategy.

## Predeclared synthetic protocol

- Generate 360 positive prices per path from a deterministic log-price simulator; start at an arbitrary USD-like scale of 2,000. Random innovations are Box–Muller standard normals times 0.007. No real gold observations are used.
- **IID**: independent innovations, a no-skill negative control. **Momentum**: autoregressive log returns with `phi=+0.50`, a positive-control signal. **Regime flip**: `phi=+0.55` before index 240 and `phi=-0.55` after, an explicit distribution shift.
- For horizons 1, 7 and 30 observed closes, compare all four *unmodified* predictors using the same origins and realized targets.
- Select the model with lowest MAE from origins starting at 80, with all target indices strictly before 240. Break exact ties in favor of persistence (listed first).
- Audit selected model only on origins at or after 240, with targets inside the generated series. Use origin stride `h` for non-overlapping target windows. Every prediction receives only the history ending at its origin.
- Score each path as `100 * (1 - selected_audit_MAE / persistence_audit_MAE)`. Report the mean across independent paths and a descriptive path-resampling bootstrap interval (400 draws), plus selection winners and the number of selection winners that lose to persistence in audit. Path-level resampling avoids treating overlapping information within a path as independent.

**Important limitation:** For `h=30`, each path has just 5 selection and 3 audit origins; even 64 independent synthetic paths cannot establish gold-market skill. The 95% bootstrap intervals quantify variation across these *simulated paths under this fixed generator*, not model uncertainty or future-market confidence.

## Reproduced diagnostic result (64 paths per scenario/horizon)

| Process | h | Mean selected-model audit skill vs persistence | Nonbaseline selection failures in audit |
|---|---:|---:|---:|
| IID | 1 | -0.50% | 33 / 43 |
| IID | 7 | -2.46% | 26 / 46 |
| IID | 30 | -8.57% | 32 / 52 |
| Momentum | 1 | +1.52% | 21 / 53 |
| Momentum | 7 | -2.02% | 31 / 49 |
| Momentum | 30 | -20.61% | 25 / 45 |
| Regime flip | 1 | -3.81% | 61 / 62 |
| Regime flip | 7 | -4.10% | 34 / 50 |
| Regime flip | 30 | -64.43% | 33 / 52 |

Local verification on Node 22: four offline tests passed; `--seeds=64` ran successfully. These figures should be rechecked in repository CI against the exact committed model version. They are not a claim of statistically significant market underperformance or outperformance.

## Decision and next useful evidence

The test demonstrates a concrete failure mode of retrospective selection: apparent selection-period winners often fail to outperform persistence on later paths, particularly after an autocorrelation reversal. Under IID returns, the mean selected-model skill is negative for all three horizons in this fixed simulation. The positive-control signal at h=1 is detectable on average, but this does not generalize across horizons.

**Do not promote a model based on these numbers.** Keep the prospective publication/close-time evidence gap separate. The next material step is independent timestamped real-world forecast issuance and outcome collection with verified provider-close semantics; only then can Gold Lab test a predeclared live comparison against persistence. Avoid additional synthetic receipt hardening unless a material bug is reproduced.
