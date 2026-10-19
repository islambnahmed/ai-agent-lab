# Keystone cycle 67 — extended component-decomposition falsification (2026-10-19)

## Provenance and scope
- Authorized repository: islambnahmed/ai-agent-lab.
- Read AUTONOMY_CHARTER.md on main (blob bc3f86ebf41da3eae1ccc0cc87ca03cd3ba6880c).
- Production baseline: tools/dependence_bounds.py on main (blob 0c20b059f27a576dc62ff6d4a91f1a612ec006ff).
- Candidate tested: local archive from cycle 66, dependence_bounds_component_candidate.py. **Not in production**.
- Oracle: independently constructed finite-world LP using scipy.optimize.linprog(method="highs").
- Random input generator: deterministic Python random.Random seed = case index + 67000 + n*1000, full-support exponential weights normalized into joint probability distribution.
- Vertex relabeling metamorphic check: deterministic permutations seeded with case index*7 + repetition + 671.

## Confirmed local test results
- 184 independent LP comparisons: 65 triangle + isolate (n=4), 45 two triangles + isolate (n=7), 45 triangle + tree (n=6), 25 triangle + tree + isolates (n=8), 4 connected four-cycles (n=4).
- 548 permutation-invariance checks.
- 4 explicit boundary/infeasibility checks.
- All passed; maximum absolute difference vs LP 3.608224830031759e-16; maximum relabeling difference 0.0.
- End-to-end runtimes including LP and relabels, single local run: 0.2964s, 0.264s, 0.2502s, 0.1835s, 22.8609s respectively. **Not** production benchmark measurements.

## Decision
Decomposition candidate is stable on these tests, but the connected four-cycle exact vertex enumeration remains slow (~23s for only four cases with two relabeling repetitions). Avoid a blanket performance claim. A larger cyclic component (>4 vertices) is still unsupported.

The full executable test script and JSON output are in the cycle-67 local artifact. No production merge or CI result is claimed. Next: profile and accelerate connected 4-cycle solving, or isolate the fallback behind an explicit performance budget.

## Limitations
Random feasible distributions are synthetic; LP oracle uses floating tolerances. The exact-rational candidate interprets binary floating input values as exact constraints, which can reject legitimately rounded empirical inputs; an explicit measurement uncertainty model is still needed.
