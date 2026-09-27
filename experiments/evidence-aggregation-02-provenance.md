# Evidence aggregation experiment 02 — provenance laundering

## Question
Is grouping evidence by immediate source enough to prevent duplicated evidence from masquerading as independent confirmation?

## Counterexample
No. Three apparently independent agents or documents can each cite the same underlying observation, test run, dataset, or report. Grouping only by immediate source would count them as independent even though their informational lineage is shared.

Example: Agent A reports CI run R; Agent B reads A; Agent C reads a dashboard derived from R. Immediate sources differ, but the root evidence is still run R. This is provenance laundering: copying evidence through intermediaries can make one observation look like several independent observations.

## Revised model
Evidence independence should be evaluated against lineage, not merely source identity. A minimal record distinguishes current source, root origin, intermediate derivations, generation method, and whether lineage is unknown. Items sharing a known root origin should not receive full independence credit merely because immediate sources differ. Unknown lineage should preserve uncertainty rather than assume independence.

## Adversarial checks
1. Three agents independently rerun the same test: potentially independent runs, so additional evidence can count.
2. Three agents repeat one run's output: shared origin, so little or no independence bonus.
3. Two papers analyze the same dataset: analysis may differ, but dataset-level errors remain correlated.
4. Two websites repeat one primary report: shared origin, not two confirmations.
5. Lineage unavailable: do not silently classify as independent; preserve uncertainty.

## Transfer
The distinction applies across CI verification, multi-agent collaboration, web research, scientific synthesis, and benchmark evaluation.

## New failure mode exposed
A provenance-aware model can still become overconfident if lineage metadata is wrong or incomplete. Provenance itself is therefore a claim requiring evidence, not trusted metadata by default.

## Next useful attack
Test whether independence should be decomposed by failure mode rather than represented as binary shared/not-shared origin. Two analyses of one dataset may share data-collection risk but have independent analysis risk.

This is an experimental reasoning artifact, not a calibrated truth metric.
