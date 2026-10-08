# Keystone — matched-fee active probes vs passive observations (2026-10-08)

**Synthetic study, not a deployed agent.** Following the passive-signal switching experiment, we tested whether active risky probes are worth the same explicit observation fee as passive noisy signals.

## Design
240 decisions; risky success probability q∈{0.50,0.95} in-model, safe expected cost 0.095, risky cost 1−q. Bayesian hazard learner (assumed hazard 1/120), prior P(high)=0.5, greedy risky threshold P(high)>0.9. 24 additional observations maximum at slots t=0,10,…,230, only if action would otherwise be safe. Each read costs 0.002. **Passive**: remain safe, buy binary 75%-accurate sensor. **Active**: take risky action to observe Bernoulli outcome, incurring decision opportunity cost. **Hybrid**: active if posterior≥0.75, otherwise passive. **None**: no extra reads. Same random risky and sensor draws across policies. 17 fixed inherited paths plus 6 predeclared holdouts, two seeds × 4,000 trajectories per scenario; cumulative dynamic-oracle expected regret including fees. Exact 60-step minimax restart comparator.

## Equal-scenario mean regret (lower is better)
| Group (n) | None | Passive | Active | Hybrid | Restart60 exact |
|---|---:|---:|---:|---:|---:|
| Inherited stationary (4) | 2.700 | **2.070** | 5.092 | 2.332 | 3.079 |
| Single switch (10) | 5.400 | **3.985** | 9.060 | 4.643 | 5.242 |
| Multi switch (3) | 5.400 | **4.931** | 9.706 | 5.821 | 10.227 |
| New holdouts (6) | **1.312** | 1.975 | 6.164 | 2.349 | 5.809 |

Passive beat active on 23/23 paths; passive beat none on only 12/23 and **lost on all six new holdouts**. Hybrid beat passive in 2/23. Active low-q probes pay expected immediate regret 0.405 versus fee 0.002. Stable-high passive regret 6.540 versus restart60 3.106; low→high at t=40 passive 5.838 versus restart60 4.006. Realized read counts differ (inherited single-switch averages passive 21.2, active 22.5, hybrid 22.1), so **equal fees and caps do not mean equal realized counts, information or total costs**.

Independent scalar implementation matched vectorized trajectories exactly in 116 pathwise comparisons (regret, read count, probe count, risky count). Separate fixed sensitivity checks used sensor accuracies .65/.75/.85 and fees .002/.010 on three paths with fresh seeds; no tuning. Main local artifacts: keystone_matched_probe_channels.py, keystone_matched_probe_channels_validation.py, keystone_matched_probe_channels_results.json, keystone_matched_probe_channels_validation_results.json, keystone_matched_probe_channels_report.md. **Those files are local unless separately committed; do not assume they are present in this branch.**

## Decision
Reject fixed-budget active probing as a universal improvement. Passive sensing helps under some switches but may make model-mismatched decisions worse. Next test an uncertainty-aware refusal gate with a no-read option, against untouched holdouts and exact restart baseline. This is not a general theorem about AI or information acquisition.