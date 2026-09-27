# Evidence aggregation experiment 03 — failure-mode independence

## Question
Is provenance lineage enough to decide whether two pieces of evidence are independent?

## Counterexample
No. Independence is not a single property of two evidence items. It depends on which failure mechanism could make both wrong.

Two analyses of the same dataset share collection and sampling risks but can have different analysis risks. Conversely, two different datasets can still share a buggy processing pipeline. A binary same-origin/different-origin rule misses both cases.

## Synthetic adversarial test
Represent each evidence item by the failure modes it depends on, then compare overlap as a diagnostic (not a calibrated probability).

- same dataset, different analyses: shared-risk overlap 0.500
- different datasets, same buggy pipeline: shared-risk overlap 0.333
- same report copied twice: shared-risk overlap 1.000
- independent replications: shared-risk overlap 0.000

The simple overlap calculation is intentionally provisional. Its value is exposing structure: different-origin evidence can remain correlated, and same-origin evidence can contain partially independent components.

## Revised model
Treat independence as conditional on failure mode.

For a claim, ask:
1. What plausible mechanisms could make this evidence wrong?
2. Which mechanisms are shared across evidence items?
3. Which mechanisms were independently regenerated or checked?
4. Which important mechanisms are unknown?

Do not collapse these answers immediately into one confidence number. Preserve a risk vector or dependency graph when the distinction matters.

## Transfer checks
- CI: separate test-code bugs, environment bugs, implementation bugs, and oracle/specification bugs.
- Web research: separate shared primary-source risk from independent interpretation/fact-checking.
- Scientific synthesis: separate dataset/measurement risk from analysis/model risk.
- Multi-agent work: separate shared context/prompt/model risk from genuinely independent observations or executions.

## New attack exposed
Failure-mode labels themselves can be incomplete or invented after the fact. A system may appear independent simply because it failed to model the shared cause. The next useful test is therefore whether unknown/common-cause risk can be represented without manufacturing false precision.

## Durable lesson
Evidence independence should not be inferred from source count or lineage alone. It is conditional on the failure mechanisms relevant to the claim.

This remains an experimental reasoning artifact, not a calibrated truth metric.
