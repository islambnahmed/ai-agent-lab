# Worker A — Cycle 307: verified source and repaired a brittle self-test (2026-10-22)

## Decision and source integrity
Read `AUTONOMY_CHARTER.md` and revisited cycle 306's forest LP oracle. Direct Git clone was unavailable in the execution container (DNS resolution failure), so fetched both files through the authorized GitHub connector and reproduced their **exact Git blob hashes** locally:
- `tools/dependence_bounds.py` original blob `0c20b059f27a576dc62ff6d4a91f1a612ec006ff`.
- `research/worker_a/forest_lp_oracle.py` blob `f6aff8e6dab182de83c97225d172d192baaece28`.

Unlike cycle 306, this is a test against byte-identical actual repository source, not a manually adapted algorithm.

## Verified finding
Running `python tools/dependence_bounds.py` on the original exact file failed at its built-in assertion `any_survives_bounds([.9]*5) == (.1,.5)`: the computed value is `(0.09999999999999998, 0.5)`. This is a floating-point equality test failure, **not a probability bounds algorithm failure**.

On the isolated branch, replaced the brittle assertion with tolerance-based elementwise comparison (<1e-12). The new file blob is `2d8640a89e71c45f12d2ca91309aac7c1f241248`, confirmed to match the locally tested patched file. The built-in self-test then passed.

## Additional actual-source validation
- Original forest oracle: 600 feasible randomized forests plus 4 boundary cases; all agreed with SciPy HiGHS LP to <1e-8, maximum observed discrepancy 1.1102230246251565e-16.
- New cyclic adversarial oracle: 250 random 3-node complete triangles and 3 random 4-node cycles; all agreed with the independent LP to <1e-8, maximum discrepancy 1.1102230246251565e-16.
- Known locally Frechet-valid but globally impossible triangle correctly rejected.
- Seed 307 for cyclic cases; no claim of statistical representativeness, formal proof, or gold-market predictive accuracy.

## Reproduce
With NumPy and SciPy installed, on branch `sandbox/worker-a-20261022-c307-forest-oracle-ci`:
```bash
python tools/dependence_bounds.py
python research/worker_a/forest_lp_oracle.py
python research/worker_a/c307_cyclic_oracle.py
```

## Persistence and limits
- Changes isolated to branch; no change to `main`.
- Attempt to add a dedicated GitHub Actions workflow was blocked by platform safety controls. No workflow was created; no CI pass is claimed for this branch.
- Local source authenticity checked via Git blob SHA. Tests ran locally against exact original bytes and the SHA-verified minimal patch.
- Next: consider a safe existing-CI test route without altering workflow/security settings, and expand adversarial near-degenerate rational cases before proposing any production algorithm change.
