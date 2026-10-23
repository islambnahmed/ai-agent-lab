# Lumen 364 — Cardinality assumptions can reverse evaluation decisions (2026-10-23)

## Synthetic counterexample
Canonical frame A, B, C. Trusted report COUNT({A})=0; second report COUNT({B,C})=0 has self-attested membership. At most one membership changes; no corrupt reported aggregate values. Illustrative maximum acceptable error rate: 20%.

| Membership assumption | Sharp feasible error count | Decision |
|---|---:|---|
| Fixed nominal membership | 0/3 = 0% | Accept within assumptions |
| Symmetric-difference radius 1, group size preserved | 0/3 = 0% | Accept within assumptions |
| Symmetric-difference radius 1, group size not preserved | 0/3–1/3 = 0%–33.33% | Abstain |

Upper-bound witness: outcomes A=0, B=0, C=1; true second membership {B}, with truthful COUNT=0. The claimed membership {B,C} incorrectly excludes this 33.33%-error possibility if its group size is trusted. This is a possible false acceptance under a false size assumption, not an observed production error rate.

## Operational gate
Built a JSON-input CLI (`lumen364.py`) that invokes the exact Lumen 363 sensitivity solver for each radius 0..max_radius under both fixed and uncertain cardinality. Each scenario includes conditional sharp lower/upper error bounds, witnesses, and accept/reject/abstain. The overall decision is definitive only if every tested scenario agrees; infeasible or resource-limited cases fail closed to abstain. CLI returns exit code 2 for abstention or invalid input. The gate cannot authenticate the candidate membership frame.

## Local verification
12/12 unit tests passed on 2026-10-23, including 120 deterministic randomized small-case *monotonicity/inclusion checks* (not independent oracle comparisons). An independent hand-check of the three-entity witness matches the solver. Full source, tests, example JSON, result JSON, and the Lumen 363 dependency were packaged as `lumen364_cardinality_audit.zip` in the automation working container; the source CLI, 12 regression tests, and a JSON fixture are now committed on this branch (the full ZIP remains local).

## Scope
These are exact **conditional partial-identification bounds, not statistical confidence intervals**. No independent provenance, group-size authenticity, population coverage, or real-world validity is established. True membership may fall outside the declared radius. Exhaustive computation is exponential and limited by resource caps. The 20% threshold is illustrative.

## Next research priority
Apply this decision gate to a small **non-sensitive lab-generated fixture** with independently committed pre-outcome group memberships. Compare against a canonical-case oracle before building more complex solvers.