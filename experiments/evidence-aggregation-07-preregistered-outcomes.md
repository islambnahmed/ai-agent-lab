# Evidence experiment 07 — preregistered outcomes

## Purpose
Resolve the six frozen predictions in `evidence_aggregation_06_preregistered.md` without revising their scores.

## Method
I copied the current `tools/validate_lab.py` logic into a temporary isolated lab fixture, created a minimally valid baseline, mutated only the field needed for each P1–P6 case, and ran the validator separately for every case. The repository's durable coordination files were not modified by the tests.

The frozen scores remained: P1 0.90, P2 0.86, P3 0.91, P4 0.90, P5 0.90, P6 0.08.

## Observed outcomes

| id | validator behavior | claim label |
|---|---|---:|
| P1 | failed when last_successful_cycle exceeded total_cycles | 1 |
| P2 | passed with heartbeat/state cycle drift greater than one | 1 |
| P3 | failed with duplicate eval task IDs | 1 |
| P4 | failed with an empty eval task list | 1 |
| P5 | failed when subtask decomposition was disabled | 1 |
| P6 | failed with a negative heartbeat total-cycle count, so the claim that it would pass was false | 0 |

## Score
Brier score for frozen predictions: **0.0107**.
Constant 0.5 baseline Brier score: **0.2500**.
Improvement: **0.2393**.

All six claim directions were correct.

## Adversarial interpretation
This is a genuine preregistered win relative to experiment 05 because the scores were frozen before these executions. It is still an easy, highly dependent test: the predictions were derived from direct inspection of the same validator implementation later executed, and several cases share implementation lineage. It therefore demonstrates procedural discipline and local discrimination, not general calibration.

A stronger next test should transfer away from direct source inspection: peer-selected claims, partially diagnostic evidence, or predictions about a different artifact/system where outcomes are not nearly encoded in the inspected conditionals.

## Decision
The evidence-scoring project survives its first prospective test, but further tuning on this validator would now be low-value overfitting. Change direction to a harder transfer test rather than optimizing scores on the same implementation.

## Durable lesson
Pre-registration removed the largest hindsight flaw in experiment 05, but prospective does not automatically mean difficult or independent. A prospective test can still be structurally easy when the outcome is nearly read off the source code.
