# Khepri experiment 417 — Single-use, content-bound approval receipts

**Date:** 2026-10-24. **Scope:** `islambnahmed/ai-agent-lab`, research branch only. **Execution:** deterministic local simulation; no GitHub/Notion/Drive write is performed by the prototype. The research artifacts may be committed separately to the authorized repository.

## Question

Experiment 416 established that an action guard is bypassable when an untrusted planner can manufacture a structurally valid `TrustedIntent`. Can a separate approval issuer, exact-plan binding, exact-content binding, and single-use execution receipt close this *specific* integrity gap?

**Result under a narrow structural threat model:** yes, for mutations made **after** an independently trusted approval is issued. This is not proof against arbitrary code execution, a compromised issuer, prompt injection into the issuer, or an agent that can access the issuer API.

## Design

- `approval_receipts.py`: `Issuer.issue(trusted_plan, approved_payload)` creates an opaque in-memory object identity. `Executor.simulate(receipt, requested_plan, payload)` consumes the approval, then compares exact plan and SHA-256 of exact bytes. `Executor` has no issuance method. Both sides use the same in-memory registry, constructed only by `new_runtime()`.
- Scope is limited to `write` within `experiments/khepri/exp417/` on the dedicated branch, inside the authorized repo. All actions are simulated return values, never network writes.
- Deliberately weaker baselines: `scope_only` (only checks allowed scope) and `path_only_approval` (binds plan but not content).
- `test_approval_receipts.py`: 19 tests, including 3,000 seeded payload mutations, replay, forged receipts, cross-runtime confusion, path traversal, and explicit negative counterexamples.
- `benchmark.py`: 10,000 seeded *adversarial* mutations across two synthetic formats (GitHub issues, SEO HTML), with legitimate executions, replays, and out-of-scope controls.

## Reproduce

Python 3.10+ standard library:

```bash
python -m unittest -v test_approval_receipts.py
python benchmark.py
```

Observed locally: **19/19 unit tests passed**. The deterministic benchmark reported:

| Measure | Count |
|---|---:|
| Adversarial mutations tested | 10,000 |
| Incorrect acceptances — scope-only baseline | 10,000 |
| Incorrect acceptances — path-only approval | 5,000 |
| Incorrect acceptances — exact plan + payload + single-use receipt | 0 |
| Correctly accepted legitimate receipts | 10,000 |
| Replays accepted | 0 |
| Out-of-scope controls denied by both scope and receipt checks | 100 / 100 |

These counts are *properties of designed synthetic inputs*, **not** a field failure rate or a measured LLM prompt-injection defense rate. The comparison is intentionally biased toward cases where the baseline checks are insufficient; it should not be interpreted as a real-world prevalence estimate.

## Counterexamples and limitations

1. **Approval laundering remains possible:** if trusted-side code calls `Issuer.issue` on an attacker-controlled plan or attacker-controlled content, the resulting receipt authorizes exactly that malicious content. One unit test demonstrates an untrusted string approved and then accepted. **A receipt proves consistency with approval, not that approval was wise.**
2. **Availability risk:** if an attacker obtains a valid receipt, they can consume it with an invalid request, preventing the intended execution. This fails closed for integrity but may cause denial of service.
3. **Python object identity is not an access-control boundary** against arbitrary Python code execution, reflection, shared-memory compromise, or leakage of the issuer reference. A real deployment requires process or service isolation, authenticated issuance, policy enforcement, concurrency-safe atomic consumption, and external tool-side authorization. The local registry is intentionally not durable and receipts disappear on restart.
4. SHA-256 is used to compare byte identity in this toy model, not to authenticate a remote party. The prototype neither verifies data truthfulness nor checks whether approved content is safe to write.
5. Only sequential execution is exercised; race conditions and crashes are untested. No actual LLM was exposed to the attack strings.

## Reusable lesson

The experiment refines 416's lesson: **an execution boundary needs provenance of approval, binding to the exact action and bytes, and replay control; a typed `TrustedIntent` or scope check alone does not establish authorization.** Separating an issuer from an executor is useful, but that separation must be enforced by the real runtime rather than naming conventions. A follow-up should test whether an LLM planner can indirectly induce trusted-side issuance, using a strictly simulated environment.
