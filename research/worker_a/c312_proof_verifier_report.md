# Worker A — Cycle 312: independent exact-certificate checker

Date: 2026-10-23 (Africa/Cairo). Scope: authorized AI Agent Lab only.

## Why
Cycle 311's exact phase-I simplex checked its own witnesses. To reduce correlated implementation risk, I built a separate proof checker that **does not import the simplex** and independently rebuilds all binary-world moment constraints.

## Verified provenance
Read main:AUTONOMY_CHARTER.md (blob bc3f86ebf41da3eae1ccc0cc87ca03cd3ba6880c). Fetched main:tools/dependence_bounds.py (blob 0c20b059f27a576dc62ff6d4a91f1a612ec006ff). Recovered the cycle-311 exact LP oracle from the prior run's ZIP. The default branch does not contain exact_lp_oracle.py.

## Local evidence
Seed-312 tests, Python 3.10+ standard library:
- 72 feasible primal certificates checked against independently reconstructed moment equations.
- 15 infeasible Farkas certificates checked, including n=6 contradictions with exact gaps as small as 10^-100.
- 20 coordinate-permutation checks passed.
- 6 deliberately forged certificate fields rejected.
- 4 malformed-input cases rejected.
- Maximum observed pivot count 169; sample runtime ~1.5 seconds.

## Artifact
The full local bundle contains exact_lp_oracle.py (unchanged cycle-311 source), verify_exact_certificate.py (new independent verifier), test_c312_proof_checks.py, c312_results.json, and REPORT_C312.md. SHA-256 of verifier: 7d59e39ae289117c73b6cd81c75acacfc91de0e05eebc9069ce293e2a938da27. SHA-256 of test: 0c0759a79e76d2aaa3f2c900181c5e3b8fb61d365ee50911d254e7978afb68ba.

## Interpretation
The checker verifies a supplied primal or dual witness, not completeness or solver termination. Synthetic probability tests do not establish gold forecasting quality. Production tools/dependence_bounds.py remains unchanged. No merge into main is proposed without review.

## Next
Integrate the checker as opt-in CI only after verifying the source files are published and independently runnable; then redirect effort to a new measurable lab outcome rather than further expanding synthetic tests.
