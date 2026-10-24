# Khepri experiment 419 — Plan binding cross-review

**Date:** 2026-10-24. **Scope:** authorized `islambnahmed/ai-agent-lab` only. **Status:** locally tested, simulated security model; no real tool calls.

## Question

Experiment 418 correctly rejects forged *receipt* objects before Python dictionary lookup. Does it also prevent a caller with a genuine receipt from changing the **approved plan** before simulated execution?

**Answer: no.** Two independent counterexamples were reproduced against the exp417 implementation and the exp418 strict-receipt adapter.

1. **Subclass-controlled equality:** `in_scope` uses `isinstance(plan, Plan)`; a `Plan` subclass can override `__eq__` to always return `True`. When the executor compares `requested != approved[0]`, an authorized path `approved.txt` can be replaced with a different in-scope path `redirected.txt`. The result reports the substituted requested path. This requires possession of a genuine receipt and the ability to pass a Python `Plan` subclass.
2. **Post-issuance mutation:** the issuer stores the original `Plan` object reference, not a snapshot. Even `@dataclass(frozen=True)` can be changed by in-process code using `object.__setattr__`. If the caller can mutate the original plan reference after issuance, both exp417 and exp418 accept the modified plan. This is an in-process reference-access precondition, not an external exploit.

An `ExplodingEqualPlan` subclass also triggers a `RuntimeError` during comparison in exp417 and exp418; exp419 rejects it before calling untrusted equality.

## Prototype mitigation

`plan_guard.py` builds on exp418's receipt-type check, but also:
- requires **exact** `Plan` type at issuance and redemption;
- snapshots approved fields into a separate `Plan` instance at issuance;
- compares primitive field tuples, not untrusted subclass equality;
- returns the approved plan's fields, not caller-controlled object fields;
- preserves one-use consumption and byte-payload digest binding.

No external writes occur. This is a **narrow Python demonstration**, not an authentication protocol, a production-grade sandbox, or a guarantee against same-process code with access to private state.

## Reproduction

Branch: `khepri/exp419-plan-binding-20261024-1156` (based on exp418, retaining exp417 as a sibling).

```bash
cd experiments/khepri/exp419
python -m unittest -v test_plan_guard.py
python benchmark.py
```

Local reproduction used exact copies of the original Git blobs: exp417 `approval_receipts.py` SHA `a82acd6be64ceaa574fc4d723c7b90a95a3dd475` (4,127 bytes) and exp418 `identity_receipts.py` SHA `0062bda383dd45a90ebe7898485bad54530df5a9` (1,179 bytes). SHA values verified with Git blob hashing. **17/17 unit tests passed** locally.

The deterministic benchmark runs **3,000 cases per variant per label** (`seo`, `gold`) for **18,000 scenario/variant cases**. Each case exercises both conditional attacks and a fresh legitimate control (54,000 redemption attempts total). For each label, original417 and strict418 accepted **3,000/3,000** subclass redirects and **3,000/3,000** mutated-plan redirects; guard419 accepted **0/3,000** of either and **3,000/3,000** fresh legitimate controls. All six variants accepted their legitimate controls. Labels are **synthetic**; no real SEO or financial system was accessed. These deliberately constructed cases are not empirical attack prevalence.

## Corrections and limitations

Exp418's receipt-identity claim remains valid **for the narrow class of forged receipts it tested**. Its protection does not imply that plan contents remain bound to the approval. Exp417's earlier post-approval integrity claim also needs this qualification.

Residual limitations: access to internal `_state` or arbitrary code execution in the same process can still defeat this model; receipt possession can still cause denial of service; mutable shared internals, races, restarts, remote authentication, issuer compromise, and LLM prompt injection are not solved. For production, use a real trust boundary, authenticated and serialized immutable approval records, atomic redemption, and tool-side authorization.

**Transferable lesson:** check both *who holds approval* and *what immutable action was approved*. Protecting a token's identity is not the same as binding its plan's semantics.
