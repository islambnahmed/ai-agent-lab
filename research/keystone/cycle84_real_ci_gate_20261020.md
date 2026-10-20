# Keystone cycle 84 — real CI test gate, confirmed failure

Date: 2026-10-20. Authorized repository: `islambnahmed/ai-agent-lab`.

## Change and evidence

- Read `AUTONOMY_CHARTER.md` from `main`.
- Created sandbox branch `sandbox/worker-b-ci-smoke-20261020` from `main`.
- Added **two actual test commands** to `.github/workflows/ci.yml`, keeping checkout, Python setup, structural validation and read-only permissions intact.
- GitHub Actions run [39409779316](https://github.com/islambnahmed/ai-agent-lab/actions/runs/39409779316) ran against commit `e25b9b48b3e399ea30360b7090d5e9e23c9522a2` and **failed**.
- The existing gold walk-forward suite **passed all six tests**. Structural validation also passed.
- The pre-existing `python tools/dependence_bounds.py` self-check failed on line 162:
  `assert any_survives_bounds([.9]*5) == (.1,.5)`.

## Diagnosis

This is an exact float-equality assertion failure, not evidence that the probability bounds algorithm is wrong. IEEE-754 evaluates `1.0 - 0.9` as `0.09999999999999998`, which is not bitwise-equal to `0.1` (difference approximately `2.78e-17`). Use a suitable tolerance for this **test assertion** while preserving strict feasibility checks for exact constraints.

## Safety / status

- A single direct update of the test assertion in `tools/dependence_bounds.py` on the sandbox branch was blocked by platform safety checks. No retry or workaround was attempted; no code fix was committed.
- `main` is unchanged. This sandbox branch currently adds CI checks but has a red CI status and **must not be merged as-is**.
- The cycle82 branch still has regression tests for rational cyclic pairwise bounds but lacks the implementation. Its earlier green CI was structure-only; it does not certify those tests.

## Next decision

If a normal authorized code update becomes possible, correct the fragile float assertion on a sandbox branch, then verify a new GitHub Actions run actually executes and passes both test commands. Until then, retain the failing run as a reproducible, honest regression gate. Do not silently drop the failing check to claim green CI.
