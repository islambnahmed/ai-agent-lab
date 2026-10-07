# Keystone: out-of-sample decision-margin gate, with abstention and false-switch constraint (2026-10-08)

## Falsification question
Does a decision-aware sequential-evidence threshold generalize to unseen action costs, and does any gain survive an explicit ~1% no-change false-switch budget?

## Protocol
Seeded, independently generated train/test Monte Carlo. Bernoulli p0=0.9; 100 post-boundary observations per path; q in {0.9,0.7,0.5,0.3,0.1}, equally weighted. Train 4,000 paths per q (seed 20261008), test 6,000 paths per q (seed 20261108). 12 training cost pairs C in {2,4,8,16}, s in {.2,.5,1}; seven *unseen* test pairs: (3,.35), (5,.65), (10,.8), (12,.3), (6,1.2), (9,1), (20,1.5). This is out-of-sample in costs and random trajectories, **not** in q distribution.

Action: risky expected loss C*(1-q), safe loss s. Oracle chooses lower expected loss. Prequential predictions: slow EWMA alpha=.03; fast EWMA alpha=.30, both initialized .9. After each observation, downward running-MLE Bernoulli GLR against p0=.9 is computed; gate opens permanently when the running maximum exceeds h. At the *next* decision, use fast if open, slow otherwise. Candidate h in {3,...,9}. Adapt baseline always uses slow.

Training chooses h by *mean regret divided by C*, to avoid raw cost-scale bias. Cost-only rule uses fixed buckets r=s/C: r<.075, .075<=r<.15, r>=.15; thresholds learned independently in each bucket. Abstaining variant may choose 'adapt' rather than a gate. Safety-constrained variant permits only h>=5 (empirically ~1% null gate crossing in this particular 100-step setting) or adapt. Bucket cutoffs and candidate families were specified for this run, not validated as optimal. All reported regrets are expected action losses under known q, not noisy realized rewards.

## Results on seven unseen cost pairs
| policy | mean normalized expected cumulative regret |
|---|---:|
| slow adaptation | **0.85334** |
| best single fixed h trained on costs (h=4) | 1.35916 |
| bucket-specific h, no abstention (h=9,9,3) | 1.15639 |
| bucket-specific h with abstention (adapt,adapt,3) | **0.84079** |
| bucket-specific h with abstention AND ~1% null constraint (adapt,adapt,5) | **0.92290** |

The unconstrained abstaining rule improves only ~1.47% over adapt on this held-out synthetic distribution. Its paired difference in normalized regret is -0.01254, 95% *conditional Monte Carlo* interval [-0.01509,-0.01000], clustering repeated cost evaluations by (q, trajectory). The safety-constrained rule is **worse** than adapt by +0.06956, interval [+0.06730,+0.07182]. These intervals do not quantify uncertainty over new q distributions, costs, or policy-class choices.

Null gate crossing by last pre-action time under q=.9: h=3: 5.88%; h=4: 2.85%; h=5: 0.97%; h=6: 0.38%; h=7-9: ~0.017% in this sample. These are empirical, horizon-specific rates, not anytime-valid bounds.

At the seven test pairs, abstention chooses slow adapt in six cases and h=3 only for (C=6,s=1.2); that pair's regret changes 16.085 -> 15.559. The gain is narrow, not broad dominance.

## Decision
**Do not promote the router as a general-purpose improvement.** Once an explicit ~1% null false-switch budget is imposed, this simple cost-bucket gate fails to beat slow adaptation on held-out cost pairs. This directly challenges the earlier optimistic cost-aware threshold story. The unconstrained improvement buys a 5.88% null crossing rate at h=3, above the proposed budget.

Do not hide this by tuning more h values. Next worthwhile falsification: compare a formally anytime-valid change e-process and a *decision-specific* false-action budget against the strong adapt baseline; separately test whether real downstream actions (model swaps, resets, irreversible decisions) justify alarms. If not, retire the router and redirect effort to a different capability-growth project.

## Reproduction and limits
Source implementation: `experiments/keystone/decision_gate_oos.py` (when committed). Requires numpy; run `python experiments/keystone/decision_gate_oos.py`. Caveats: synthetic Bernoulli process, fixed 100-step horizon, no gradual changes, same q grid in training/test, no model-selection uncertainty in confidence intervals, and an empirical h>=5 budget that must be recalibrated for other horizons.