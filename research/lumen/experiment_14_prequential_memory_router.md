# Lumen Experiment 14 — Prequential Memory Routing (2026-10-08)

## Hypothesis
Choose memory horizon without ground-truth labels by selecting the model with the best **past-only** predictive log loss on 21 source-pair agreement events. This could retain long-memory stability while reacting to source-topology drift.

## Method
- Seven synthetic sources; a five-source correlated-wrong bloc shifts from indices 0–4 to 2–6, either stable or with a 100-step ramp.
- Each policy sees only source-answer vectors, never the simulated truth. The evaluator uses truth only after predictions.
- Four candidate histories: cumulative, rolling 24, rolling 60, exponentially decayed (0.95).
- Score candidates by Beta(1,1)-smoothed pairwise Bernoulli log loss over the **previous 24 observations**. Select lowest score. A conservative variant prefers longer history within 0.01 nats/pair.
- Cluster partitions recomputed every four rows from past history only. Predictions are made before adding the current observation.
- Initial exploration: 12 seeds per condition (12 conditions). **Independent holdout**: 24 new seeds per case for four selected cases. Post-transition accuracy counts abstentions as incorrect; coverage reported separately in JSON. Paired intervals use a normal approximation over per-seed deltas; they are descriptive, not preregistered confirmatory inference.
- Holdout seeds start at 20,000,000. All simulations are synthetic, and the source-generating process is known to the evaluator.

## Independent holdout: post-transition accuracy

| Case | Router | Cumulative | Rolling 24 | Rolling 60 | Exp 0.95 | Conservative router |
|---|---:|---:|---:|---:|---:|---:|
| Exact / stable | 79.86% | 82.08% | 65.69% | 76.04% | 71.74% | 82.08% |
| Near-copy / stable | 69.03% | 79.86% | 39.24% | 60.00% | 44.37% | 77.29% |
| Exact / gradual shift (ramp 100) | 60.14% | 0.00% | 60.00% | 38.61% | 54.65% | 60.00% |
| Near-copy / gradual shift (ramp 100) | 26.67% | 1.94% | 23.89% | 18.82% | 16.11% | 25.83% |

Router minus rolling-60 paired 95% normal intervals:
- Exact stable: +3.82 pp [0.28, 7.36]
- Near stable: +9.03 pp [1.17, 16.88]
- Exact gradual shift: +21.53 pp [17.99, 25.06]
- Near gradual shift: +7.85 pp [3.37, 12.33]

Critical comparisons:
- **Near-copy stable:** router **underperforms cumulative by 10.83 pp**, interval [-16.11, -5.56] pp.
- **Near-copy gradual shift:** router beats rolling-24 by only 2.78 pp, interval [-1.21, 6.77] pp; improvement is not resolved.
- Exact gradual shift: router is indistinguishable from rolling-24 (+0.14 pp, interval [-2.01, 2.28] pp).

## Interpretation
A label-free router can react to changing source-dependence statistics and substantially outperform a stale long-memory policy after drift. However, **predicting source agreement is not the same as predicting truth**. In stable near-copy conditions, the router forgets too eagerly and loses to cumulative memory; after difficult gradual near-copy drift, accuracy remains low (~27%). No evidence of universal adaptive superiority.

## Important limitations
1. The evaluation is on a single synthetic seven-source family with a known generator; it is not evidence of general truth detection.
2. Candidate choice uses source-answer agreement, which can reward coordinated misinformation.
3. No external ground-truth feedback is available to the router.
4. All methods share a restricted clustering/prediction rule, and some runs abstain.
5. The oracle reference used in older experiments should **not** be treated as an upper bound during a mixed-topology transition: it assumes one complete bloc before the ramp finishes.
6. Pilot cases informed the holdout case selection; the 24-seed holdout is independent but the scenario family was not independently chosen.

## Next falsifiable experiment
Compare agreement-log-loss routing against a **calibrated abstention + evidence acquisition** policy: when models disagree, abstain or spend a limited truth-query budget. Evaluate risk/coverage, cost per correct answer, and behavior under systematic shared bias. Include a null condition where no independent truth signal exists.

## Reproduction
Local artifacts from the run:
- `lumen_prequential_router_14.py`
- `lumen_prequential_router_14_results.json`
- `lumen_router_14_holdout.py`
- `lumen_router_14_holdout_results.json`

Run the scripts alongside `lumen_gradual_drift_13.py` with Python 3 standard library only. Local files are **not** claimed to be in GitHub unless separately committed.
