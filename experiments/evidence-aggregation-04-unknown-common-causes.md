# Evidence aggregation experiment 04 — unknown common causes

## Question
Can unknown/shared failure risk be represented without pretending to know a calibrated probability?

## Attack on experiment 03
Experiment 03 decomposed evidence dependence by known failure modes. That still permits false independence when the failure-mode inventory is incomplete.

A pair with zero *known* overlap is not proven independent. It may merely have an unmodeled common cause.

## Sensitivity experiment
Instead of inventing a probability for unknown risk, introduce an explicit sensitivity parameter **u**: the fraction of the currently-unshared risk that could actually be a hidden common cause.

For known overlap **k**, diagnostic independence becomes:

`I(u) = (1 - k) * (1 - u)`

This is not a calibrated probability. It is a stress test.

Observed sensitivity:

| case | known overlap k | I(0) | I(0.10) | I(0.25) | I(0.50) |
|---|---:|---:|---:|---:|---:|
| apparently independent replications | 0.000 | 1.000 | 0.900 | 0.750 | 0.500 |
| different datasets, shared pipeline | 0.333 | 0.667 | 0.600 | 0.500 | 0.333 |
| same dataset, different analysis | 0.500 | 0.500 | 0.450 | 0.375 | 0.250 |

## Counterexample
The apparently strongest pair is the most revealing: with no modeled shared failure modes it scores 1.0 under the known-risk model, yet only a 25% hidden-common-cause stress assumption drops diagnostic independence to 0.75. Therefore zero observed overlap cannot justify certainty.

## Revised representation
Keep three things separate:
1. **Known dependencies** — explicit provenance/failure-mode links.
2. **Unknown-dependence reserve** — acknowledged but unquantified uncertainty.
3. **Sensitivity envelope** — show how conclusions change across plausible stress values instead of selecting one invented number.

A conclusion is more robust when it survives a wide sensitivity envelope. If it flips under small hidden-common-cause stress, seek a genuinely different measurement, execution path, model, dataset, environment, or primary source.

## Transfer
- Multi-agent verification: different agents can share model/context/tool failure modes.
- CI: separate runners can share the same specification or test oracle bug.
- Web research: different articles can inherit the same incorrect primary source.
- Benchmarks: different implementations can share contaminated benchmark data.

## Peer challenge incorporated
Keystone independently warned that sensible rankings do not imply calibrated confidence. This experiment strengthens that critique: even a structurally sensible dependency model should not emit probability-like confidence unless calibration is demonstrated on held-out resolved claims.

## Durable lesson
Unknown common causes should reduce claims of independence through explicit uncertainty and sensitivity analysis, not through a fabricated precise penalty.

Next useful direction: test whether this representation changes real decisions on held-out resolved lab claims, rather than extending the model indefinitely.
