# Lumen 360 — Robust bounds with noisy overlapping aggregates (2026-10-23)

Synthetic, deterministic follow-up to Lumen 359. This is a **sharp partial-identification interval**, not a confidence interval.

## Research question and method
If up to `k` reported OR/COUNT aggregate **values** are adversarially wrong, but the canonical entity frame and group memberships are authentic, which entity-level error rates remain feasible?

Enumerate binary entity assignments, count contradicted aggregate values, retain only assignments contradicting at most `k` reports, and minimize/maximize the total errors. Branch-and-bound prunes on already-forced contradictions and objective bounds. Return concrete endpoint assignments and names of disputed groups. Malformed reports and registry mismatches are rejected even when `k > 0`. Search-budget exhaustion raises an error without returning uncertified bounds.

## Verified six-entity counterexample
Canonical entities A,B,C,D,E,F. Reports: OR(A,B)=1; OR(B,C)=1; OR(A,C)=1; COUNT(E,F)=1; OR(C,D)=0.

| Maximum corrupt values | Sharp errors | Sharp rate | DFS nodes, both endpoints |
| --- | --- | --- | --- |
| k=0 | 3..3 | 50%..50% | 26 |
| k=1 | 2..5 | 33.33%..83.33% | 38 |
| k=2 | 1..6 | 16.67%..100% | 26 |

Even **one possible corrupted aggregate** turns a point-identified 50% risk into 33.33%–83.33%. At a 40% acceptance threshold, the all-trusted evidence rejects while k=1 cannot justify either acceptance or rejection. This widening is an epistemic cost, not evidence that corruption occurred.

## Reproducibility and tests
Standard-library Python prototype `lumen360.py` and `test_lumen360.py` are in conversation artifact `lumen360_noisy_overlaps.zip`, alongside `results.json`, report, test log and SHA256SUMS. Command: `python -m unittest -v test_lumen360`.

**10/10 tests passed.** Independent exhaustive oracle agreed across **500 seeded random small instances** (2–8 entities), including feasible and infeasible cases; endpoint witnesses and disputed reports were verified. Seed 360. ZIP integrity verified.

## Limitations and next work
- Assumes binary entity outcomes, correct canonical frame, correct memberships, and no more than k adversarial *values*. A caller-provided membership registry is not independent attestation.
- If k is understated or membership is tampered with, the guarantee fails.
- Worst-case search is exponential; no production-scale claim.
- Next: independently committed membership snapshots and corruption model sensitivity, plus scaling tests on sparse overlapping graphs.

**Status:** Executable source and tests were subsequently committed to this branch at `research/lumen/lumen360.py` and `research/lumen/test_lumen360.py`; the local ZIP remains the exact locally tested and checksummed bundle.