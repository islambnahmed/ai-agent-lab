# Worker A — C328 independent holdout mutation audit

Date: 2026-10-23. Base: `sandbox/worker-a-20261023-c327-mutation-audit`. Offline-only work; no external HTTP requests or change to `main`.

## Question

Did C327's **22/22 (100%)** result generalize beyond the 22 mutants used to improve its own tests?

## Method

Before adding new fixtures, define **14 distinct, named, one-at-a-time holdout source mutations** in `run_c328_holdout.py`. None are from the 22 C327 mutants. Run them against the existing C326 fixtures, C327's four targeted fixtures, and the independent C327 prefix/wildcard reference oracles. Mutants are loaded from in-memory copies of the trusted parser; the repository parser is never overwritten. No network I/O.

**Unmodified holdout result: 6/14 killed (42.9%), 8/14 survived.** Surviving classes were byte-limit and path-length boundary equality, invalid fragments, infix user-agent matching, colon inside rule values, multi-parameter URL queries, HTTP URL acceptance, and URL with empty path.

Eight focused post-holdout cases were then added. **Post-targeted result: 14/14 killed**. The 100% number is an *in-sample repair score*, not a holdout score. It is not a guarantee of correctness, general mutation coverage, RFC 9309 conformance, or production readiness.

## Important integrity failure detected and corrected

The first generated 500 KiB boundary fixture was accidentally **512,002 bytes**, yet labeled `disallowed`. The unmodified parser correctly returned `unknown`, because its inspection limit is 512,000 bytes. That mislabeled fixture falsely appeared to kill almost every mutant. **The preliminary inflated score is invalid and was discarded.**

The fixture was corrected to exactly **512,000 UTF-8 bytes**. The runner now checks *all* fixture labels against the original, unmutated parser **before** evaluating mutants, and aborts on any mismatch. A regression test deliberately supplies a mislabeled fixture and verifies that the benchmark rejects it. The path boundary fixture is exactly **8,192 characters**. This validates internal consistency, not external truth of the expected labels.

## Verification

Local execution on the extracted C327 source bundle:

- C328: **4/4 unittest methods passed**, including eight subcase fixtures and a bad-label rejection check.
- C327: **3/3 unittest methods passed**.
- C326: **4/4 unittest methods passed**.
- Holdout mutations: **6/14 killed before new cases; 14/14 after eight new cases**.
- No production parser code changed. No GitHub CI run. No network requests.

Reproduce on this branch:

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c327:research/worker_a/c328 python -m unittest discover -s research/worker_a/c328 -p 'test_c328*.py' -v
python research/worker_a/c328/run_c328_holdout.py
```

## Decision

The generalization claim from C327 should be **downgraded**: selected-mutation 100% did not generalize to new fault classes. The C328 fixture-integrity guard is reusable and should be applied to other mutation benchmarks. The next meaningful work is an independent semantic reference implementation or a separate reviewer of the fixture labels, rather than repeating a 100% score against hand-targeted mutants. Keep the network transport experimental.
