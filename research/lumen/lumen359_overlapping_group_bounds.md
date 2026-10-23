# Lumen 359 — Overlapping aggregate groups and sharp entity-risk bounds (2026-10-23)

Synthetic, deterministic continuation of Lumen 358. No production data or independently authenticated lineage.

## Correction and counterexample
For canonical entities A,B,C,D,E,F, observe OR(A,B)=1, OR(B,C)=1, OR(A,C)=1 and COUNT(E,F)=1. The sharp number of entity errors is **[3,5] out of 6** (50%–83.33%), not the sum of overlapping group contributions. The positive triangle forces at least two errors in A,B,C; D is unconstrained, and exactly one of E,F is an error.

Lower witness: A=0,B=1,C=1,D=0,E=0,F=1. Upper witness: A=1,B=1,C=1,D=1,E=1,F=0. Both reproduce every aggregate.

Add OR(C,D)=0. Then C=D=0, A=B=1, and exactly one of E,F=1. The sharp interval collapses to **[3,3] out of 6** (50%). An overlapping negative observation can fully identify the entity error count.

## Implementation and verification
Standard-library Python exact binary OR/COUNT constraint solver with propagation, branch-and-bound minimization/maximization, and concrete feasible endpoint witnesses. It rejects inconsistent observations, malformed groups, membership mismatches against a supplied registry, and search-budget exhaustion (never returns uncertified partial bounds).

**12/12 tests passed.** An independent brute-force oracle checked **320 deterministic random instances** with n=2..8, feasible and infeasible overlapping groups, matching every result. Initial test expected [3,4], but a valid D=1 upper witness showed that expectation was wrong; corrected to [3,5] and reran all tests.

## Limits and recovery
Exact binary outcomes, canonical frame, and honest group memberships are assumed. A caller-supplied trusted registry is *not* independent authentication. The interval is partial identification, **not a confidence interval**. Search is worst-case exponential; default 200,000-node cap. Complete source, tests, results and SHA256 manifest are in the conversation artifact `lumen359_overlapping_group_bounds.zip`; not yet published to GitHub.

Next: noisy overlapping aggregates and independently attested membership snapshots.
