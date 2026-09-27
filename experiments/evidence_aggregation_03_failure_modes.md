# Evidence aggregation experiment 03 — failure-mode independence

## Question
Is shared root provenance enough to decide whether two evidence items are independent?

## Result
No. Independence is not one binary property. Two items can share one failure mode while remaining independent on another.

## Model
Represent each evidence item as exposure to failure-mode families rather than only a source/root identifier. Example families:
- data_collection
- implementation
- environment
- analysis
- interpretation
- reporting

For a pair of evidence items, extra confirmation should be discounted only for the failure modes they plausibly share. Unknown exposure remains uncertainty rather than being treated as independence.

## Counterexamples
1. Two papers analyze the same dataset with different methods: data-collection risk is shared; analysis/implementation risk can be partly independent.
2. Two CI jobs run different tests on the same commit and same runner image: implementation/test logic may differ, environment and code-under-test risks are shared.
3. Two agents independently rerun the same specification against independently implemented code: specification/interpretation risk may remain shared even when implementation risk differs.
4. A manual reproduction and an automated test on the same environment: method risk differs, environment risk is correlated.
5. Two websites citing different papers that both use the same benchmark dataset: immediate provenance differs while dataset-level risk remains shared.

## Practical rule
Do not ask only "Are these independent?" Ask "Independent with respect to which plausible way the claim could be wrong?"

A confirmation adds the most information when it attacks failure modes not already covered by existing evidence.

## Implication for lab verification
When choosing a second check, prefer diversity of failure modes over repetition count. For example, after CI passes, a useful follow-up may be a negative test, independent implementation, manual reproduction, or specification review depending on which failure mode remains uncovered.

## Limitation
Failure-mode labels are themselves hypotheses. A taxonomy can create false precision if it is treated as exhaustive. Keep an explicit unknown/other bucket and revise the taxonomy when counterexamples appear.

## Next experiment
Turn this qualitative model into a small challenge set: given an initial piece of evidence and several candidate follow-ups, rank which follow-up reduces uncovered failure risk most. Compare the ranking against a simple "count independent sources" baseline.
