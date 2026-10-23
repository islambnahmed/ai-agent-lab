# Lumen 363 — Missing membership alternatives can reverse evaluation decisions (2026-10-23)

## Research question
Lumen 362 computes sharp partial-identification bounds *conditional on an explicitly listed candidate set*. What if the list is incomplete, even though the group size is known? This cycle tests the hidden completeness assumption by replacing self-attested candidate lists with a **sensitivity envelope**: allow any nonempty membership within a symmetric-difference radius of the nominal group, optionally preserving group size, with at most `b` groups changed and `k` corrupted aggregate values.

## Verified synthetic counterexample
Six canonical entities A–F and seven overlapping COUNT/OR reports are used from Lumen 361–362. The authentic `g2={B,C}`, `COUNT=0` produces exactly **3/6=50%** error under fixed memberships. A self-attested but altered `g2={A,D}` with the *same reported value* produces exactly **1/6=16.67%**. This is a false acceptance at a 25% maximum-error threshold if the altered membership is accepted as authentic.

| Nominal g2 | Size-preserving symmetric-difference radius | Sharp feasible errors | At 25% max-error threshold |
|---|---:|---:|---|
| authentic {B,C} | 0 | 3/6 = 50% | Reject |
| altered {A,D} | 0 | 1/6 = 16.67% | **False accept** if the true group is {B,C} |
| altered {A,D} | 2 (one replacement) | 1/6–2/6 = 16.67%–33.33% | Abstain |
| altered {A,D} | 4 (two replacements) | 1/6–3/6 = 16.67%–50% | Abstain; includes authentic outcome |
| authentic {B,C} | 2 | 1/6–3/6 = 16.67%–50% | Abstain |

**Important nuance:** radius 2 around {A,D} does **not** include authentic {B,C} (their symmetric difference is 4). Although radius 2 happens to block acceptance at a 25% threshold, it still excludes the actual 50% case and could falsely accept at a 40% threshold. Sensitivity bounds are valid only when the true membership is in the declared envelope. No finite envelope proves this independently.

## Implementation and verification
`lumen363.py` implements a standard-library-only exact outcome-enumeration and dynamic-programming solver over membership-change and value-corruption budgets. It is algorithmically independent of the Lumen 360/362 solvers, providing an additional oracle-style check. It emits feasible lower/upper outcome and membership witnesses and fails closed when option/work budgets are exhausted. `test_lumen363.py` contains six unit tests, including **350 deterministic randomized small-instance comparisons** against a separate exhaustive Cartesian-product oracle (seed 363). All six tests passed locally on 2026-10-23. `results.json` is in the local ZIP with full witnesses and deterministic work counters. Run `cd research/lumen && python -m unittest -v test_lumen363 && python lumen363.py`.

## Scope and caveats
- These are **sharp conditional partial-identification bounds**, not statistical confidence intervals. Binary outcomes and fixed canonical entity identities are assumed; only COUNT/OR aggregates are supported.
- The model allows a group to have any nonempty membership inside the specified Hamming/symmetric-difference radius; `preserve_group_size=True` assumes true cardinality is known. At most `b` groups can differ from nominal; at most `k` report values can be corrupt.
- No independent pre-outcome provenance, group-size authenticity, population coverage, or real-world behavior is established. An attacker can misreport both nominal membership and allowable radius.
- Exhaustive outcomes are exponential in entity count (explicit maximum 24); membership options may also be exponential. Resource caps raise `SearchLimit` without a misleading partial result.

## Decision and next experiment
Do **not** certify favorable risk solely from an evaluator-supplied candidate list. Require a separately controlled pre-outcome membership commitment where available; otherwise report a **radius/budget sensitivity curve**, explicitly label assumptions, and abstain when decision changes under plausible alternatives. Next: stress-test **wrong group-size assumptions** and combine uncertain membership with unknown canonical frame membership. Avoid repeated complexity growth without an operational use case.
