# Evidence aggregation experiment 01

Question: how can an agent avoid turning weak or duplicated evidence into false certainty?

## Counterexample found
A normalized signed-weight prototype returned confidence 1.0 whenever the only available evidence supported the claim, even when that evidence was stale and indirect. Therefore relative normalization alone is invalid for confidence calibration.

## Revised prototype
Keep a neutral uncertainty prior and aggregate evidence strength against that prior. Correlated repeats from the same source and direction are grouped so repetition does not masquerade as independence.

Synthetic checks:
- weak-only evidence -> 0.558
- strong direct evidence -> 0.662
- same-source evidence repeated three times -> 0.631
- two independent supporting sources -> 0.718
- supporting evidence plus stronger reproducible counterevidence -> 0.463

## Transfer implication
For claims such as "CI proves the implementation works", repeated green outputs from one workflow should not be treated like independent confirmation. A manual reproduction, negative test, or independent implementation can add materially different evidence.

This is an experiment, not a truth metric. Numeric weights are provisional and should be challenged or replaced if calibration tests fail.
