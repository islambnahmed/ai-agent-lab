# Experiment 009 — Closure: minimal reproducers

## Capability obtained
A compact failure minimizer for sequence-like cases, with a ddmin-style search and explicit distinction between 1-minimal and globally minimum results.

## Corrections learned
1. Greedy deletion can get trapped in a larger local minimum.
2. ddmin-style chunk/complement search improves exploration but still does not promise a global optimum.
3. Flaky predicates invalidate the assumption behind deterministic reduction.
4. Repetition can gate noisy reproduction, but correlated noise means repeated votes are not automatically independent evidence.
5. Structured inputs need structure-aware reducers; blind sequence deletion can generate meaningless candidates.

## Why stop
The next improvements would be domain-specific: AST reducers for code, event reducers for traces, JSON-aware reducers, or statistical models for flaky tests. Building all of them without a concrete failing artifact would be infrastructure speculation.

Reopen only when a real failing case needs shrinking. Then build the smallest structure-aware transform required by that case.

## Status
Candidate source artifacts; no executable PASS is claimed without an execution environment.
