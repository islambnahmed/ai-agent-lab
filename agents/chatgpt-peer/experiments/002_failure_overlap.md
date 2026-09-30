# Experiment 002 — Failure overlap

## Question
Can two methods with identical individual error rates have very different value when combined?

## Construction
A fails on 4 of 8 cases. Compare:
- B1: fails on exactly the same 4 cases.
- B2: fails on the opposite 4 cases.

Both B1 and B2 have a 50% failure rate, so an individual accuracy summary cannot distinguish their relationship to A.

## Result
For A+B1, joint-failure lift relative to an independence baseline is 2 and phi is +1.
For A+B2, joint-failure lift is 0 and phi is -1.

So equal marginal quality can hide radically different failure structure. A weaker-looking method can sometimes add more complementary information than a duplicate strong method; marginal score alone is insufficient for composition decisions.

## Counterexample / limitation
With only four observations, perfect-looking association can occur and should not be treated as reliable evidence. The tool describes observed overlap; it does not prove causality, statistical independence, or a shared root cause.

## Artifact
`tools/failure_overlap.py`

## Status
Candidate until its executable test is actually run.
