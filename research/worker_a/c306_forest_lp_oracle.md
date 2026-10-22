# Worker A — Cycle 306: forest-bound differential oracle (2026-10-22)

## Decision
Changed direction after repeated gold-data provenance and calibration audits duplicated peer work. Tested a distinct, reusable probability-bounds capability: whether the forest fast path in `tools/dependence_bounds.py` agrees with an independent full-joint linear program.

## Method
- Read the existing forest-feasibility theorem and the current `tools/dependence_bounds.py` implementation on `main` (commit `8d8b4be50acc22e94882610d834e6f17b459b275`).
- Independently optimize the mass of the all-ones world over `2^n` Bernoulli atoms, subject to marginal and supplied pairwise moment equalities, with SciPy HiGHS. The LP does not call or derive its objective from the forest formula.
- Deterministic seed 306: 150 feasible random joint laws at each of n=3,4,5,6 (600 cases). Reveal only an acyclic subset of pairwise moments, including disconnected forests.
- Add four degenerate boundary cases (all variables identical with probability 1/2), and a deliberately impossible edge as a negative control.
- Local run used a manually transcribed copy of the repository's forest branch, not a byte-identical checkout. The committed reproducibility script imports the **actual repository module** when run in a checkout; this distinction matters.

## Local result
- 600/600 randomized feasible cases agreed within 1e-8.
- 4/4 degenerate cases agreed; invalid edge was rejected.
- Maximum absolute discrepancy: `1.1102230246251565e-16` (floating-point roundoff).
- This is **differential evidence**, not a proof of the theorem or of correctness for all inputs.

## Reproduce against actual repository code
From repository root, with optional research dependencies installed:
```bash
python -m pip install numpy scipy
python research/worker_a/forest_lp_oracle.py
```
The script is intentionally separate from production runtime dependencies and CI; no CI success is claimed. It performs no network requests.

## Limits / follow-up
- Cases were generated from known feasible full joint distributions. They do not probe globally infeasible cyclic moments, large-n solver behavior, or near-infeasible numerical adversaries.
- For stronger validation, run the committed script in a fresh checkout and inspect CI evidence before promoting this to a regression gate. Then add adversarial cyclic examples with a separate feasibility oracle.
- No change to `main`, no new gold forecasts, and no inference about market performance.

## Artifacts
- `research/worker_a/forest_lp_oracle.py` — reusable independent oracle.
- Branch: `sandbox/worker-a-20261022-c306-forest-oracle`.
