# Experiment 007 — Failure-case minimization

## Question
Can a large failing sequence be reduced automatically to a small reproducer?

## Result
A deletion-based reducer can remove irrelevant material until no single deletion preserves failure. A ddmin-style reducer adds chunk/complement search before final one-by-one reduction.

## Important distinction
"1-minimal" means no *single* remaining item can be deleted while preserving failure. It does **not** mean globally smallest.

Counterexample predicate: failure occurs when Q is present OR when A+B+C are all present. A deletion-order-dependent greedy reducer can retain A+B+C even though [Q] is a smaller failing case.

## Value
Useful for shrinking logs, test inputs, rule sets, or collections of conditions before debugging.

## Limits
- Predicate must be reproducible enough for repeated evaluation.
- Stateful/flaky failures can mislead the reducer.
- Sequence deletion may be invalid for structured inputs unless structure-aware transforms are used.
- Global minimum is not guaranteed.

Artifact: `tools/failure_minimizer.py`.
Status: candidate pending actual execution.
