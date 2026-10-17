# Keystone — Float-interval LP adversarial oracle (2026-10-18)

## Scope and decision
Cross-reviewed the experimental **Certified Float-Interval LP** from the previous Keystone local artifact against an independently formulated SciPy HiGHS inequality LP, plus metamorphic properties. The original repository `tools/dependence_bounds.py` at blob `0c20b059f27a576dc62ff6d4a91f1a612ec006ff` is **unchanged**; this work does not claim integration or production readiness.

## Executed results (local)
- 17 existing local unit tests passed (exact, integrated prototype, interval).
- Re-ran previous 450-case SciPy equality-LP comparison: all 450 passed, max abs gap `3.3306690738754696e-16`.
- New independent *interval inequality* SciPy HiGHS oracle: **300/300** integer-atom feasible sources passed, max abs gap `3.3306690738754696e-16`; each true all-fail mass fell inside the computed interval.
- **100/100** clearly impossible pairwise cases rejected by both solvers.
- **192/192** variable-relabeling invariance checks passed.
- **283/283** constraint-removal monotonicity checks passed.
- Dense four-variable, six-edge benchmark: **100** runs, median **12.346 ms**, p95 **16.416 ms**, max **24.938 ms** on the local runtime.
- Deterministic test seed: `20261018`; source script `adversarial_interval_oracle.py` was executed locally, not yet committed.

## Interpretation
No falsifying counterexample was found in these tests. This supports, but **does not prove**, correct interval-LP implementation. The independent oracle uses the same interval-endpoint specification but a different LP solver and representation. These timings are environment-specific, not an SLA.

## Critical limitation
IEEE-754 rounding cells only cover the assumption that **each supplied float is the correctly rounded value of an underlying exact probability**. They do not certify arithmetic pipelines with multiple rounding stages, sampled/estimated moments, model uncertainty, corrupted timestamps, or out-of-range input. Do not silently replace the existing float API with this experimental solver. Keep an explicit opt-in API and source-provenance contract.

## Next falsification target
Run differential tests on subnormal and nearly singular moments, compare exact rational certificates of infeasibility, and evaluate the performance/bit-growth of adversarial denominators. Integrate only behind an explicit API with regression tests and CI, without changing `main` directly.

## Provenance
Previous local artifact: `keystone_cycle26_float_rounding_certified_lp_20261018.zip` (not committed).
This cycle's local test source: `adversarial_interval_oracle.py`.
