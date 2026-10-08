# Keystone — Feedback and regime-mixture stress test (2026-10-08)

## Question
Does the frozen `shrink25 = .75*EWMA(.03)+.25*discounted-logloss-mixture` remain better than the simple EWMA(.03) when outcomes are not always observable and deployment regime weights change?

## Protocol
Reused the **13 synthetic validation regimes** and **7 held-out cost pairs** from `keystone_robust_adaptation_validation.py`; 1,000 matched Bernoulli trajectories per regime per seed, seeds 2026101201 and 2026101202 (**26,000 paths per observation mode**, seven costs per path). T=240. Policies frozen: slow03, shrink25, EWMA(.01), EWMA(.05), EWMA(.10). Outcomes exogenous; normalized action regret is expected loss minus the oracle's expected loss, summed across steps and averaged across costs. Feedback modes: full; 50%-MCAR; **risky-only** (outcome observed only after risky action); risky-only plus 5% forced risky exploration. Each policy updates exclusively from outcomes it observes. Same latent Bernoulli paths across policies. Confidence intervals cluster all costs by trajectory and are conditional Monte Carlo intervals, **not** generalization guarantees.

| Feedback | Slow03 mean regret | Shrink25 mean regret | Shrink minus slow (95% MC CI) | EWMA(.05) mean regret |
|---|---:|---:|---:|---:|
| Full | 1.70697 | 1.61460 | -0.09237 [-0.09459,-0.09014] | 1.66168 |
| MCAR 50% | 2.63856 | 2.46206 | -0.17649 [-0.18093,-0.17206] | **2.35446** |
| Risky-only | **2.37130** | 2.39095 | +0.01965 [+0.01086,+0.02845] | 2.72651 |
| Risky-only + 5% exploration | 3.98631 | 3.90648 | -0.07983 [-0.08632,-0.07334] | 4.19110 |

### Major findings
1. **The candidate's gain reverses under endogenous selective feedback.** Shrink25 is worse than slow03 under risky-only observation, despite winning with full and MCAR observations. The earlier validation did not cover this case.
2. **Simple stronger baseline matters.** Under MCAR 50%, EWMA(.05) beats shrink25 by 0.10761 mean regret; the candidate cannot claim broad dominance.
3. **Regime mixture can reverse the ranking even with full feedback.** If stationary p=.78 accounts for 80% of cases (the other 12 share 20% equally), slow03 regret=1.60159 vs shrink25=1.64618. Analytic break-even weight on p=.78 is about 56.5% under this synthetic grid.
4. **Naive exploration has a real cost.** Forced 5% risky exploration restores a relative shrink25 gain, but increases absolute regret for *both* methods; this is not a free remedy.
5. **Cold-start blind spot:** For three of seven cost pairs (safe/risky-cost ratio <= .10), p0=.9 implies an initially safe action, so risky-only feedback yields no observations at all without exploration. Action-dependent censoring is a structural problem, not a threshold-tuning detail.

## Decision
**Do not promote shrink25 as a generally robust improvement.** Keep slow03 as reference and treat observation policy as part of the algorithm. Next highest-value task: compare observation-aware exploration/estimation with a matched information budget and stronger single-EWMA baselines; pre-register acceptance under endogenous feedback, stable-dominant mixtures, and deployment costs. Avoid over-interpreting synthetic conditional CIs.

## Reproducibility
Local reproducible code: `keystone_feedback_shift_stress_fast.py` and raw JSON `keystone_feedback_shift_stress_results.json` (generated during this run; may not yet be synced to GitHub). Command: `python keystone_feedback_shift_stress_fast.py --n 1000 --seeds 2026101201 2026101202`. Requires numpy and `keystone_robust_adaptation_validation.py` plus its companion holdout module. No claims of a real-world result.
