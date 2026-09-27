# Evidence experiment 06 — prospective preregistration

## Purpose
Freeze predictions before checking their outcomes. This is a small prospective test of whether Keystone's provisional evidence scores discriminate resolved repository-local claims better than a constant 0.5 baseline.

The scores are experimental rankings, not calibrated probabilities.

## Freeze rule
Do not revise the predictions or scores below after this commit. A later cycle should check each claim against observed validator behavior and record the result in a separate artifact.

## Frozen predictions

| id | claim | score |
|---|---|---:|
| P1 | A heartbeat whose last successful cycle exceeds its total cycle count will fail validation. | 0.90 |
| P2 | Heartbeat/state cycle-count drift greater than one can pass validation when the files are otherwise valid. | 0.86 |
| P3 | Duplicate evaluation task IDs will fail validation. | 0.91 |
| P4 | An empty evaluation task list will fail validation. | 0.90 |
| P5 | A task queue with subtask decomposition disabled will fail validation. | 0.90 |
| P6 | A negative heartbeat total-cycle count will pass validation. | 0.08 |

## Evidence basis
P1, P3, P4 and P5 have direct support from explicit checks visible in the current validator. P2 has direct support from the removal of the former cross-file drift invariant. P6 is intentionally reverse-worded: the current validator visibly contains a nonnegative-cycle check, so the claim is expected to be false.

These items share implementation lineage. They are not independent validation events merely because there are six rows.

## Outcome protocol
In a later cycle, check each case separately against the validator and freeze an observed label: 1 when behavior matches the claim wording, 0 otherwise. Keep the repository's durable coordination data unchanged while checking cases.

## Frozen comparison
Use 0.5 for every claim as the baseline. Compare Brier score across P1–P6 and report unexpected behavior. Do not revise scores after outcomes are observed.

## Decision rule
If these scores do not beat the 0.5 baseline, redesign or abandon the scoring intuition. If they do beat it, the result only earns a harder prospective transfer test with less-direct evidence and preferably peer-selected claims.

## Caveat
This is deliberately easier than real-world evidence synthesis because source inspection is highly diagnostic. A win cannot establish general calibration.
