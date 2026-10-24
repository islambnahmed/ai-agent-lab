# Lumen 389 — Gold prospective-claim gate: truthy evidence flags can produce false eligibility

**Date:** 2026-10-24 (Africa/Cairo). **Scope:** `islambnahmed/ai-agent-lab`, branch `sandbox/worker-c`.

## Goal and why the direction changed

After Lumen 388, further hardening the optional JSON validator offered diminishing returns. I instead audited an actual decision-relevant tool: `research/lumen/cycle342_prospective_claim_gate.py`, which screens whether supplied Gold Lab prospective evidence is *eligible for scoring*. A false eligibility result could mislead downstream research even though the tool expressly does not authenticate vendor evidence.

## Reproduced failures on synthetic inputs

Constructed a valid synthetic one-observation receipt/evidence pair and then varied one field at a time. The original implementation returned `eligible_for_scoring` for:
- the string `"false"`, string `"yes"`, or integer `1` in **each of four** supposed independent-verification flags, because Python treats them as truthy;
- `horizon: 1.0` because `1.0 == 1` despite a horizon intended to be an integer;
- a missing source/provider on both sides, or matching empty, null, or numeric providers, because equality alone was used.

The initial local adversarial suite had **17 failing subtest assertions** across 8 test methods. These are synthetic input-validation counterexamples, **not evidence of forged GitHub/vendor provenance in the wild**.

## Minimal correction

- Require `evidence.get(flag) is True` for all four verification flags, rejecting strings, numbers, absent keys, and false values.
- Require `type(horizon) is int` and membership in `(1, 7, 30)`.
- Require a nonempty string `receipt.source`, rather than allowing both sides to be absent or malformed.
- Keep existing chronology, observation-sequence, provider-match, and numerical-error checks.

The corrected source and synthetic tests were run locally with Python ordinary and `-O`: **8/8 test methods passed in each mode**, plus successful `py_compile`. This is **16 test-method executions**, not 16 independent test cases. Tests use only fabricated provider values and timestamps. The source and test blobs published to GitHub were confirmed to match the locally tested `git hash-object` values:
- Source blob `6879a681891e7cc1010ae5535033d8ed4ced7ecc`, code commit `e03c91ec76274cbc969d4f84206326d5b84a6fc2`.
- Test blob `084903557634ff1b359f97e0126be1469ddb0845`, test commit `3852254e8be0f91bd0eb3acfb319c8bd21662329`.
- CI workflow commit `43cc57c37d91603a7e0e9b51dcb09598ab68d8f0` adds normal and optimized claim-gate tests to the existing Lumen regression workflow on Python 3.12/3.13. Workflow permissions remain `contents: read`; no security settings changed.

## Boundaries and interpretation

A result of `eligible_for_scoring` still means **only** that user-supplied claims pass internal structural screening. Anyone supplying `true` flags can still falsely assert independent verification. The gate does not download source observations, inspect historical vendor vintages, verify a GitHub timestamp, or attest independent custody. **No live gold forecast, model skill, or trading edge was established.**

The correct next work is to obtain independently verifiable source evidence and test prospective predictions against a persistence baseline, or develop a narrowly scoped transfer-case benchmark with actual evidence. Avoid another generalized validator or receipt wrapper without a new failure mode.

## Reproduce

From `research/lumen`:
```sh
python -m unittest -q test_cycle342_prospective_claim_gate.py
python -O -m unittest -q test_cycle342_prospective_claim_gate.py
```

**GitHub CI status at initial report drafting:** the exact workflow commit's runs were observed as `in_progress`, not yet verified successful:
- [Lumen regression run 40099523303](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40099523303)
- [AI Agent Lab CI run 40099523310](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40099523310)

No unrelated repository, credentials, accounts, or external content were accessed.

## Verified CI follow-up (same day)

The exact workflow commit `43cc57c37d91603a7e0e9b51dcb09598ab68d8f0` completed **success** in both [Lumen regression run 40099523303](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40099523303) and [AI Agent Lab CI run 40099523310](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40099523310). The Lumen run's job metadata confirms the new **Screen synthetic Gold Lab evidence claims (normal and optimized)** step succeeded separately under Python **3.12** and **3.13**, alongside the existing disposable-copy regression step. These are 8 test methods in each of two modes for each of two interpreters (**32 method executions**), not 32 unique cases. This is a tested synthetic contract, not authenticated provider evidence or a production forecast result.
