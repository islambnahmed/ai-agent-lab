# Khepri Experiment 385 — Untrusted Evidence Cannot Mint Tool Capabilities

Date: 2026-10-23. Scope: AI Agent Lab only. No external action or real model was executed.

## Question
Can a deterministic controller prevent instructions embedded in tool outputs (web pages, CI logs, retrieved documents) from being promoted into write permissions, including resource-alias attacks?

## Method
Built a local reference implementation with immutable per-action/per-path grants, controller-supplied provenance, fail-closed canonical repository paths, and segment-boundary subtree matching. Compared against a deliberately vulnerable regex parser and naive string-prefix scope checking. Evaluated 6,000 seeded adversarial text cases (2,000 per domain; 1,500 per encoding/quoting variant), 50,000 valid paths plus 50,000 adversarial mutations, and 21 unit tests.

## Reproduced results
- 21/21 unit tests passed.
- Baseline regex parser promoted 3,000/6,000 untrusted snippets into proposed actions, including 1,500 explicitly quoted historical examples. It did not parse the remaining 3,000 obfuscated/encoded snippets.
- Of 3,000 parsed snippets, 996 path-traversal or neighbor-prefix escapes passed naive startswith scope checking.
- Provenance-gated guard allowed 0/6,000 tool-output-origin proposals, including requests targeting otherwise granted paths; it allowed 100/100 separately generated trusted-planner writes within grant scope.
- On 50,000 seeded valid paths and 50,000 mutated paths, strict guard accepted 50,000 valid paths and rejected 50,000 mutations. Naive prefix check accepted 45,000 of the mutations.

## Falsification / limitations
1. This is a deterministic reference model, **not an LLM jailbreak evaluation**. The vulnerable baseline is a regex-to-action parser, not a deployed agent.
2. The origin tag must come from a trusted runtime; untrusted retrieved text must not be allowed to forge it.
3. The executor must use the exact canonical path approved by the guard. Downstream re-decoding or path resolution can reintroduce bypasses.
4. A malicious or overbroad **trusted** plan remains dangerous; this guard is not an intent classifier.
5. This does not prevent indirect contamination of an LLM planner's reasoning or summaries.
6. POSIX-style repository paths are not equivalent to Notion/Drive ancestry. Those resources need verified lineage, not textual prefix checks.

## Transferable lesson
Retrieved text is evidence, not authority. Runtime-attested provenance and narrow trusted capability grants must control actions. Normalize and validate resources before checking action/path scope. A cheap and reversible test can expose naive prefix-scope bugs.

## Reproducibility
Local bundle: khepri_exp385_reproducible.zip, containing capability_firewall.py, test_capability_firewall.py, benchmark.py, fuzz_paths.py, REPORT.md, results.json, fuzz_results.json. Commands: python -m unittest -v test_capability_firewall.py; python benchmark.py; python fuzz_paths.py. Seed: 3852026 (benchmark), 385 (fuzzer).

## Follow-up
Test with a real agent/tool adapter and stub executor; challenge metadata authenticity and time-of-check/time-of-use behavior before production adoption.
