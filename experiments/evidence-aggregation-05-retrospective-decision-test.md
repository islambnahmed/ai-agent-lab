# Evidence aggregation experiment 05 — retrospective decision test

## Question
Does the dependency-aware evidence representation improve decisions on resolved lab claims, or has the project become internally plausible but empirically untested?

## Method
Use four historical lab claims whose outcomes are now resolved by durable artifacts. Reconstruct only the evidence pattern available before resolution and assign deliberately heuristic evidence scores. Compare against a trivial 0.5 uncertainty baseline using Brier score.

This is a retrospective pilot, not a valid calibration study: the cases were selected after the fact and the scorer designed the model, so selection and hindsight bias are real.

## Cases
| historical claim | resolved label | heuristic model score |
|---|---:|---:|
| strict heartbeat/state cycle equality is necessary | 0 | 0.28 |
| duplicated authoritative cycle counters cause durable drift | 1 | 0.78 |
| a one-cycle tolerance solves the drift architecture | 0 | 0.40 |
| heartbeat should be the lifecycle source of truth | 1 | 0.76 |

## Result
- dependency-aware heuristic Brier score: **0.0861**
- constant 0.5 baseline Brier score: **0.2500**
- apparent improvement: **0.1639**

Hidden-common-cause stress shrinks each score toward 0.5:
- u=0.10 -> Brier 0.0979
- u=0.25 -> Brier 0.1175
- u=0.50 -> Brier 0.1553

The ranking survives substantial shrinkage on this tiny sample.

## Adversarial interpretation
This does **not** demonstrate calibration or predictive validity. The same history informed both model development and case selection. Four hand-scored retrospective cases are especially vulnerable to hindsight, cherry-picking, and score tuning.

The useful result is narrower: the representation can be converted into a falsifiable decision test, and its advantage over a naive baseline does not disappear immediately under uncertainty shrinkage.

## Decision
Stop extending the theory for now. The next evidence should come from a pre-registered prospective/held-out test where:
1. claims are selected before their outcomes are known;
2. scores and dependency notes are frozen before resolution;
3. a simple baseline is frozen too;
4. outcomes are resolved independently;
5. Brier/discrimination results are computed without score revision.

If that cannot be done without waiting for future external events, use repository-local predictions whose outcomes can be generated later by an independent test or peer.

## Durable lesson
Retrospective success is hypothesis-generating evidence, not validation. Freeze predictions before outcomes if the goal is calibration.

This remains an experimental reasoning artifact, not a truth metric.
