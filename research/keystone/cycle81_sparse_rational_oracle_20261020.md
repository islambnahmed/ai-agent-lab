# Keystone cycle 81 — sparse exact-count LP oracle audit

**Date:** 2026-10-20. **Scope:** authorized `islambnahmed/ai-agent-lab` only. `main` unchanged.

## Verification gap closed

Cycle 80 showed 155/400 guaranteed-feasible sparse 4-event distributions rejected after independently rounding their marginals and pairwise joints to floats. The `Fraction` candidate accepted all 400, but its **optimal bound values** had not been independently checked on that sparse corpus.

Ran 400 deterministic sparse distributions (seed 130; 2–7 nonzero integer-count atoms out of 16; all six pairwise joints). Compared the locally archived cycle-80 rational solver's lower/upper all-fail bounds with independent SciPy HiGHS numerical LP minimization and maximization over 16 atoms.

- **400/400** cases matched the independent LP oracle at tolerance `1e-7`; **zero mismatches**.
- Largest absolute discrepancy across 800 endpoints: **3.33e-16**.
- Local candidate runtime: median **0.0038 s**, p95 **0.0055 s**, max **0.0075 s** (not a generalized benchmark).
- Converting the same rational marginals and joints independently to floats again caused **155/400** strict-input rejections (104 pairwise Fréchet, 51 LP infeasibility), consistent with cycle 80.

## Limits and decision

SciPy is a floating-point oracle, not an exact proof near infeasible boundaries. This result validates the **tested sparse rational bound values**, not arbitrary inputs or end-to-end production behavior. The candidate implementation and reproducible script remain in the local cycle-81 archive, not asserted as uploaded. `main` remains unchanged.

**Next:** preserve the explicit exact-count/`Fraction` contract; run repository CI and review a sandbox integration before any production merge. Do not silently apply a float tolerance to strict rational inputs.
