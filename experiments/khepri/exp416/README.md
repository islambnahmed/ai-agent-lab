# Khepri experiment 416 — Untrusted Tool-Result Boundary

**Date:** 2026-10-24. **Scope:** authorized AI Agent Lab only. **Execution:** local, synthetic, reversible; **no external tool calls or production actions** in the experiment. This is a direction change from numeric/refresh/evaluation experiments 406–415 to a reusable **agent tool-output trust-boundary** prototype.

## Research question

Can a small deterministic action boundary prevent instructions embedded in retrieved text from changing the tool action selected by a separately trusted plan, while still extracting useful typed facts?

**Answer within the stated model: yes.** The action is computed only from `TrustedIntent` fields. `ToolResult.body` is parsed into **data observations** and JSON-serialized with an explicit untrusted label. It cannot affect the `Decision` value through the code path in `route`.

## What was built

- `boundary.py`: a typed intent, an allowlist for one experiment branch and directory, safe path-component checks, bounded JSON-serialized untrusted observations, and two data extractors (`github_issue` first line, `seo_html` title).
- `test_boundary.py`: 17 unit/property tests including 5,000 seeded arbitrary-text mutations, malformed paths, Unicode compatibility characters, JSON role spoofing, source spoofing, and invalid Unicode.
- `benchmark.py`: 8,000 additional seeded synthetic tool-result variants split evenly between GitHub-issue-like and SEO-HTML-like input; includes out-of-scope negative controls and a deliberate counterexample.
- `results.json`: the recorded deterministic benchmark output.

The code never executes a GitHub/Notion/Drive write; `route` returns a simulated decision and extracted data. This proof-of-concept restricts to one specific GitHub branch and directory; it does **not** claim to cover the whole user-authorized lab.

## Reproduction

From this directory, with Python 3.10+ (stdlib only):

```bash
python -m unittest -v test_boundary.py
python benchmark.py
```

Observed: **17/17 tests passed**; **0/8,000** synthetic cases changed the selected action; **0/8,000** produced malformed typed observations; **3/3** explicit out-of-scope negative controls denied. A separate property test exercised **5,000** mutations. These numbers are **not** empirical prompt-injection defense rates for language models; they verify deterministic invariants of this prototype.

## Counterexample — scope is not provenance

An unsafe planner can read a line from an untrusted GitHub issue, build a `TrustedIntent` from that line, and submit it to the guard. If the chosen path stays under the allowed directory, the guard allows it even though the request was **not** genuinely trusted. The benchmark demonstrates this with `experiments/khepri/exp416/overwrite.md`.

**Therefore:** this guard is not a complete prompt-injection defense. It enforces a structural action boundary **only when the caller already preserves provenance of the trusted plan**. A later LLM reading JSON-encoded untrusted data may still follow embedded instructions; JSON labeling does not prevent that. Nor does the guard assess whether extracted observations are factually true, or whether an in-scope write is desirable.

## Competing explanation / caveats

The zero-change result is expected by construction because the action depends only on `TrustedIntent`; it is an invariant demonstration, not evidence that a general-purpose AI model resisted an adversary. Malicious content can still manipulate a model **upstream** of intent creation, and structured data can be false. Practical use needs separate trusted-plan provenance, human/policy approval for high-impact actions, domain-specific schema validation, and end-to-end tests with actual agents before any deployment.

## Lessons and next experiment

1. Keep tool results as typed observations, not executable instructions or authority-bearing role metadata.
2. Validate the requested operation, repository, branch, and path **at the point of execution**; do not trust an earlier prompt-level assertion.
3. Do not confuse a type name like `TrustedIntent` with proof of trusted origin.
4. Next: test whether a real agent planner can be induced to manufacture in-scope intents from untrusted observations; compare provenance-preserving vs contaminated-plan designs, without any live writes.
