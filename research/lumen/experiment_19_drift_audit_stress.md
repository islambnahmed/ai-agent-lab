# Lumen Experiment 19 — Drift, Truth Audits, and a Failure of Event-Triggered Verification (2026-10-08)

## Question
Does the frozen Experiment-18 strict dependence-change guard generalize to gradual drift? With equal test-label budgets, does moving truth checks earlier when observed evidence looks unusual outperform regular audits?

## Design and boundaries
- Synthetic binary truth, 3 reporting channels, 120 training + 120 test rounds per episode. Seven regimes; **250 new paired episodes per regime** (seeds 24000000–24000249), then **250 more independent replication episodes** (27000000–27000249). Thus 500 episodes / 60,000 decisions per regime across the two batches.
- All trained policies share 24 truth-labeled *training* examples. The 18-style strict guard uses **zero test labels**. The two new audit policies each use **exactly 12 test truth labels** (one per ten-round block), with the label revealed **after** the current prediction. No policy receives future test labels.
- Comparators: untrained majority; static anchored-24; **frozen strict guard from Experiment 18** (48-observation past-only agreement window, pair agreement >78%, gap >20 percentage points, six consecutive detections, change only from no baseline pair); periodic audits at t=9,19,...,119; and event audits earlier within each ten-round block on disagreement/uncertainty or agreement change, otherwise at the block deadline.
- New audit-based decision rule is *exploratory*: accuracy-weighted votes with exponentially updated per-source reliability after audited labels, pair weight halving when dependence is detected, abstention on low confidence. Both audit policies use the same predictor and equal label budget.
- Per-decision loss = wrong + 0.30×abstention + 0.02×test-label requests, divided by 120. **Shared training-label acquisition cost is excluded**, so the majority baseline is not a full cost-matched comparison. Pairwise approximate 95% intervals are calculated over 250 paired episode losses in the primary batch, not over correlated individual decisions.

## Primary independent batch — decision loss (lower is better)

| Regime | Majority | Static anchored | Frozen strict guard | Periodic audit | Event audit |
|---|---:|---:|---:|---:|---:|
| Stable independent | .05987 | .06007 | .06020 | .07815 | .08049 |
| Stable unequal quality | .04093 | .04093 | .04093 | .04687 | .04787 |
| Abrupt A/B dependence | .45897 | .45910 | **.28843** | .23385 | **.22610** |
| Gradual A/B dependence | .25847 | .25863 | .23097 | .19566 | **.19238** |
| Gradual all-source shared errors | **.25847** | .25863 | .25863 | .27530 | .27771 |
| Gradual quality reversal (two strong → weak, one weak → strong) | **.14200** | .14200 | .14200 | .16858 | .16763 |
| Silent truth-label drift, unchanged report statistics | .32600 | .32620 | .32613 | **.31291** | .32265 |

### Paired comparisons and replication
- **Frozen guard vs static anchored:** abrupt A/B improvement **−.17067** loss/decision (95% interval [−.18063, −.16070]); gradual A/B **−.02767** ([−.03196, −.02338]). In the independent replication, the corresponding improvements were **−.17127** and **−.03090**.
- **Event vs periodic audit:** abrupt A/B **−.00775** ([−.01478, −.00072]), replicated **−.00950** ([−.01686, −.00214]); the benefit in gradual A/B was small and inconclusive (**−.00328**, interval [−.00862, .00207]), replicated **−.00245** (interval crosses zero).
- **Silent truth drift:** event auditing was **worse** than periodic by **+.00974** ([+.00566, +.01382]); replicated **+.00617** ([+.00186, +.01048]). Observable disagreement cannot reliably signal a change in the mapping from reports to truth. Earlier event-triggered checks can spend their one-per-block label budget before the most informative late observations.
- **Gradual all-source shared errors:** guard did not improve on static. Periodic and event auditing also underperformed majority in total decision cost. **Gradual quality reversal:** the guard never switched and both audit-based rules were worse than static. Do not generalize an A/B improvement into broad drift robustness.
- Guard switched at least once in **95.6%** of abrupt A/B episodes (mean first switch t≈38.9), but only **74.0%** of gradual A/B episodes (mean t≈92.7), **0.4%** of gradual all-source episodes, and **0%** of quality-reversal episodes.

## Interpretation
The previous guard has a real but narrow strength: detecting a new, uniquely over-agreeing pair. It is not a general truth-change detector. **The larger correction is that an apparently more intelligent event-triggered audit scheduler can be reliably worse than simple periodic verification when the underlying truth changes without a visible signature.** A stable periodic exploration floor remains important; agreement-driven verification alone is insufficient.

New audit policies also have an undesirable trade-off: they abstain more often and can lose on stable environments despite lowering the fraction of outright wrong decisions. For example, on stable independent data, periodic audit cost .07815 versus majority .05987; audit-based error among answered decisions was .06828, not a clear quality improvement.

## Validity / limits
This is a synthetic family with fixed, hand-specified drift forms and prices; the policies were not tuned on these two seed blocks, but the task design and policy family are exploratory. Approximate confidence intervals are descriptive and do not correct for seven regimes / multiple comparisons. The labels in the simulator are exact, not delayed or corrupted. The study does **not** demonstrate general causal dependence detection, reliable truth discovery, or deployed agent autonomy.

Seven local regression tests passed. Two independent 250-seed batches reproduced the key positive (abrupt A/B) and negative (silent truth drift) effects. A prior self-test incorrectly assumed two short example sequences had no distinctive pair; it was corrected before either batch was executed. No failed test is counted as evidence.

## Reproduction and checkpoint
Locally executed standard-library Python artifacts:
- `lumen_drift_audit_19.py` — SHA-256 `69b8d0cc6efa8019fe63640799db18dbf3e538676e88c215a979e4fc8173d5a1`
- `test_lumen_drift_audit_19.py` — seven passing tests
- `lumen_drift_audit_19_results.json` — SHA-256 `58f42b979e053ff6aa0cbb0e8ef30e3e8e32a280d9085723244ec511c604f9c1`
- `lumen_drift_audit_19_replication.json` — SHA-256 `fb56d9dad3ba5efda81768db78fd987a40ccc8b4a3439a5bf250369992e39517`

The report is committed here; **do not infer that the local executable artifacts are in GitHub** from this report.

## Next falsifiable direction
Design a **mixed verification scheduler** with an inviolable periodic floor plus a small *additional or reallocatable* event budget, tested under equal total label costs. Compare it to periodic and event-only policies on a predeclared mixture of observable and silent drift, including delayed/corrupted audits. Reject it if it fails worst-case loss or risk–coverage constraints on unseen regimes. Avoid optimizing only mean performance on abrupt pair drift.
