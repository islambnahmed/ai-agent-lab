# Lumen cycle 228 — late-label reserve and expiring truth evidence (2026-10-17)

## Decision
**Experimental only.** The new hybrid reduces the worst observed cost regret across seven synthetic worlds, but performs materially worse than cycle 227 on persistent abrupt drift. It is not a universal or production default.

## Protocol and selection
Three binary auditors; 100 unlabeled training reports; 160 held-out decisions; at most 18 truth labels; audit cost 0.10 error-equivalents. Prediction always precedes its own truth label. Only audit disagreements between majority and C. Cycle 227 hybrid: 9 scheduled informative audits + 9 triggered, and C selected on >=2 advantage among last 8 audited disagreements without expiry.

Cycle 228 candidate: **15 scheduled informative audits + at most 3 triggered**; discard audit evidence older than **40 decisions**; require at least 4 recent audited disagreements and >=1 C error advantage to choose C. Unchanged drift detector: past 32 disagreement rate differs from 100-report training rate by >0.12 for three consecutive decisions. Scheduled informative audits may be delayed/skipped, so this is a maximum budget.

Explored 5 candidates on 120 seeds per world (2280000..2280119). Selected the candidate with smallest *maximum observed world regret* before a fresh 500-seed-per-world holdout (22800000..22800499). Seven synthetic worlds, **3,500 holdout episodes**. Cost=(wrong predictions + 0.10×audits)/160. Regret relative to best observed policy per world among baselines and candidates; descriptive only.

## Fresh holdout means (lower better)
| World | No audits | Cycle 227 hybrid | Cycle 228 | New minus 227, paired 95% normal CI |
|---|---:|---:|---:|---|
| Stable | 0.061312 | 0.068742 | 0.071307 | +0.002565 [0.002264, 0.002866] |
| Abrupt persistent A/B failure | 0.339687 | 0.184650 | 0.201446 | +0.016796 [0.013676, 0.019917] |
| Gradual A/B failure | 0.240287 | 0.164059 | 0.163161 | -0.000897 [-0.004135, 0.002340] |
| A/B improve, C weakens | 0.046462 | 0.057712 | 0.057818 | +0.000105 [-0.000002, 0.000212] |
| C improves, A/B weaken | 0.144762 | 0.115975 | 0.102053 | -0.013923 [-0.015803, -0.012042] |
| Whiplash (C good t40–94, bad after t95) | 0.095200 | 0.117642 | 0.109387 | -0.008255 [-0.011290, -0.005220] |
| Transient A/B shared failure t50–99 | 0.188537 | 0.174446 | 0.141297 | -0.033149 [-0.035384, -0.030914] |

Worst-world regret (over these seven worlds): old hybrid **0.033149**, new **0.016796**; mean regret old 0.012727, new 0.007476. Despite improved worst-world regret, new policy is worse than no audits in stable, A/B-improvement, and whiplash worlds. It also loses to old hybrid on persistent abrupt drift. No generalization to unseen worlds established.

## Verification
23 local unit tests passed (8 new + 15 inherited), including audit budget, deterministic replay, no current/future truth leakage, no future report leakage, evidence expiry, and cost accounting. 350 additional new-test episodes passed budget assertions. No live agents, credentials, real SEO data, or production systems used.

## Reproducibility
Local artifact: `lumen_cycle228_reversal_reserve.zip` contains Python standard-library sources, tests, exploration228.json, holdout228.json, report228.md, SHA256SUMS_228.txt. Run `python -m unittest -v test_lumen_reversal_reserve.py test_lumen_hybrid_truth_audit.py test_lumen_truth_anchor_budget.py`. Reproduce the holdout with `run(500,22800000,{'expiry40_floor15':dict(floor=15,burst=3,max_age=40,min_labels=4,margin=1)})` in `lumen_reversal_reserve.py`.

## Limits and next falsification
Toy worlds selected by researchers; hindsight oracle comparator; per-world normal CIs unadjusted for multiple comparisons; audit-label reliability assumed perfect; soft late reserve. Next: previously unseen multiple reversals, noisy/delayed truth labels, and robustness under regime uncertainty. Do not deploy from these results.
