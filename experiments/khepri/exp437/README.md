# Khepri exp437 — untrusted tool-output authority laundering

**2026-10-25 | synthetic, offline | Python standard library**

## Question

Can an AI agent treat instructions embedded in a tool result as authorization to expand its allowed action scope? **Not safely.** Tool results are evidence, not a control-plane source of permission.

## Pivot

After three consecutive experiments on point-in-time data leakage (434–436), this cycle deliberately moved to **agent action authorization**. This tests a materially different failure class: tool-result instructions attempting to redirect the next write.

## Reusable prototype

`authority_gate.py` defines a frozen `Intent`, a fail-closed `check()` over the three authorized lab surfaces, and a guarded tool-output handling path that never converts an observation into authority. The GitHub policy permits reads and new file creation on `khepri/*` experiment branches, but not writes on `main` (a conservative experimental policy, not a claim that `main` is user-forbidden). Drive/Notion use exact root IDs and do not assume descendant access without separately verified ancestry.

`unsafe_follow_tool_text()` and `unsafe_prefix_gate()` are **deliberately vulnerable baselines**, not recommended implementations. They demonstrate two mistakes: parsing `ACTION_JSON` from untrusted text as a command, and allowing actions based only on string prefix checks.

## Evidence

Run `python -m unittest -v test_authority_gate.py` and `python benchmark.py`.

- **10/10 unit tests passed**.
- **6,000 synthetic tool-output injections** (2,000 per GitHub/Drive/Notion surface, sampled from **18 distinct crafted variants**): weak prefix gate accepted 6,000/6,000 unauthorized proposals; strict direct policy gate accepted 0/6,000; guarded tool-output handler retained the original authorized intent in 6,000/6,000.
- **6 legitimate representative intents** passed strict policy.
- **3,000 randomized legitimate actions** passed; **3,000 corresponding authority-field/path mutations** were rejected.

These are constructed adversarial inputs, not 6,000 independent attack techniques or evidence about actual LLM attack success rates. The weak baseline intentionally ignores operation semantics, so its failure rate is not a population estimate.

## Counterexamples / limits

1. **Compromised planner**: the strict policy still rejects out-of-scope actions even when they originate from the nominal planner, as long as every tool invocation goes through the gate.
2. **In-scope harmful content**: a legitimate file-create operation carrying malicious instructions in its file contents is *allowed* by this authority-only gate. Content validation, human review, and side-effect policies are separate controls.
3. **Tool-identity spoofing**: if the execution layer itself falsely marks untrusted text as trusted, this in-process design cannot establish provenance; enforce separation at the actual tool invocation boundary.
4. **No descendant inference**: child Drive folders and Notion pages need verified ancestry. The conservative exact-root policy sacrifices some authorized functionality to avoid trusting forged ancestry.
5. Path rules are intentionally strict (reject percent escapes and backslashes), potentially excluding some harmless filenames. Real integration must validate the exact target after canonicalization by the platform API.

**Lesson:** authority belongs to a separate, immutable control plane. Do not let tool outputs rewrite policy; validate the final typed action at the tool boundary. No real GitHub/Drive/Notion mutations were performed by the benchmark.
