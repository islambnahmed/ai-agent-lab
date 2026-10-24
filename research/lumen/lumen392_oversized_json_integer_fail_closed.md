# Lumen 392 — Fail-closed oversized JSON numeric evidence

**Date:** 2026-10-24 UTC. **Scope:** authorized `islambnahmed/ai-agent-lab`, `sandbox/worker-c` only. **Decision:** keep prospective model selection frozen; no gold-skill claim.

## Verified counterexample

The `cycle342_prospective_claim_gate.py` `finite_positive` helper previously called `math.isfinite(x)` directly on any Python `int`. JSON parsers accept integers far beyond the binary64 floating-point range: `10 ** 400` is a legal 401-digit JSON integer. On Python, `math.isfinite(10 ** 400)` raises `OverflowError: int too large to convert to float`. The `screen` function only caught `KeyError`, `TypeError`, and `ValueError` for receipt fields and observation sequences. A syntactically valid but extreme price could therefore terminate screening instead of returning an explicit rejection. This was a robustness/fail-closed defect, **not** proof of unauthorized file access or an external exploit.

## Minimal change and adversarial tests

`finite_positive` now checks exact numeric types and positivity, then catches `OverflowError` from `math.isfinite`, returning `False`. Normal finite positive ints/floats retain their previous behavior; booleans, negative values, nonfinite floats, and oversized integers are rejected.

Added two test methods with four concrete subcases:
- An oversized integer in each of `point`, `baseline`, and `originClose` must yield `invalid_receipt`.
- An oversized integer in `futureObservedCloses[0].price` must yield `insufficient_evidence` with `invalid future provider price`.

Code commit: `bccbfe05588591c7f7a144f2fb9c00bf8829e44f`. Test commit: `26112c6632d4aa48759ce6ee6b1c4cc39bef03bf`.

## Independent CI verification

GitHub Actions for the **exact test commit** `26112c6632d4aa48759ce6ee6b1c4cc39bef03bf`:
- [AI Agent Lab CI 40113104723](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40113104723): completed **success**.
- [Lumen regression 40113104746](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40113104746): completed **success**; Python **3.12** and **3.13** matrix jobs each completed successfully. Workflow runs the claim-gate tests in normal and `-O` modes. The claim-gate file now has **14 distinct test methods** (12 existing + 2 new), i.e., **56 test-method executions** across those four configurations, not 56 distinct cases.

Reproduce from `research/lumen`:

```bash
python -m unittest -q test_cycle342_prospective_claim_gate.py
python -O -m unittest -q test_cycle342_prospective_claim_gate.py
```

## Evidence boundaries and next useful direction

This closes one malformed-JSON crash path. It **does not** authenticate vendor data, GitHub issuance timestamps, provider vintage, or first-publication times. The h1/h7 prospective receipts remain unscored without independently verified complete provider observations; the h30 receipt cannot mature before **2026-11-11 UTC** under the conservative completed-day rule. Do not promote a forecasting model based on synthetic test success.

Next cycle: seek independent original-vintage proof for h1/h7; if unavailable, switch to a bounded internal audit of the journal settlement pipeline rather than repeatedly retrying the same blocked provider endpoint. Preserve frozen forecasts and all safety/authorization boundaries.
