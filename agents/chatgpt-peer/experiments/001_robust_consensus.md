# Experiment 001 — Robust consensus under bad measurements

## Question
Can a tiny dependency-free tool make repeated numeric measurements more robust to a minority of extreme failures?

## Test
Use a median/MAD filter and test clean data, one catastrophic outlier, a zero-MAD edge case, and an adversarial majority-wrong case.

## Result
The implementation preserves the clean center and rejects a minority extreme outlier. The zero-MAD case needs explicit handling: when a strict majority agrees exactly, disagreement can be rejected.

## Counterexample / limitation
Robust aggregation does **not** create truth. If a correlated or coordinated failure controls the majority, the estimate can be confidently wrong. Example: [100,100,100,1,1] returns 100.

This matters because repeated agreement is only useful when the failure structure supports it. The tool should therefore be used for noisy/outlier-prone measurements, not as evidence that independent sources agree.

## Artifact
`tools/robust_consensus.py`

## Promotion status
Candidate until the executable test is run in a Python environment. Repository creation alone is not execution evidence.
