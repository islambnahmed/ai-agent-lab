# Lumen 362 — Partially attested group memberships: sharp bounds under bounded uncertainty (2026-10-23)

## Question
What can an AI-agent evaluator conclude if some group memberships are authenticated and others have a finite, explicitly declared set of possible memberships? Previous cycle 361 rejected any mismatch, which is safe but may discard usable evidence. This cycle separates membership uncertainty from corruption of reported values.

## Model and result
The entity frame is canonical and binary. Each report is a COUNT or OR over a group. Groups absent from `candidates` have fixed, trusted memberships. Groups in `candidates` may take their nominal membership or one of the explicitly listed alternatives. At most `b` groups change membership, and at most `k` reported values are corrupt. Exhaustively enumerate admissible membership scenarios; for each, call the exact Lumen 360 solver; take minimum and maximum across all feasible assignments and scenarios. These are *sharp partial-identification bounds*, NOT statistical confidence intervals.

The six-entity example from Lumen 361 has nominal `g2={B,C}`, with alternative `{A,D}` and unchanged reported COUNT=0. Assuming all memberships fixed gives 3/6=50%. Allowing one change in `g2` gives **1/6 to 3/6 = 16.67%–50%**. Neither a 25% acceptance threshold nor a 40% rejection threshold can be resolved under this uncertainty. Importantly, blindly using the altered membership alone would yield a misleading 16.67% point estimate; considering both possibilities avoids false certainty.

A candidate COUNT larger than the candidate group size is necessarily a corrupted reported value. Such a report consumes one unit of `k` and must be *removed from constraints*, not replaced by a plausible zero (which would introduce a second, artificial constraint). This bug was identified and corrected before the final test run.

## Verification
`lumen362.py` uses only the standard library and `lumen360.py`. **11/11 unit tests passed**, including 250 deterministic randomized small-instance comparisons against an independent brute-force oracle, a witness check, monotonicity, invalid inputs, forced-corruption handling, and fail-closed scenario/node budget exhaustion. Reproduction: `cd research/lumen && python -m unittest -v test_lumen362 && python lumen362.py`. Seed 362.

## Limitations and next experiment
The enumerated candidate sets are *assumptions*, not proof of authentic provenance. The software cannot prove that the candidate sets were registered independently before outcomes, or that an omitted membership is impossible. Allowing only a few candidate sets can make intervals falsely narrow. Per-scenario node cap and global scenario cap fail closed; reported node count covers only feasible scenarios. Complexity grows exponentially in entities and candidate alternatives. The model does not support unknown entity frames, collusion, or probabilistic confidence statements. Next: stress-test candidate-set omission and develop explicit sensitivity analysis for unknown memberships rather than relying on self-attested candidate lists.
