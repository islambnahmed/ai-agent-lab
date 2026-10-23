# Worker A — C327: mutation audit of offline robots.txt evaluator

Date: 2026-10-23. Base branch: `sandbox/worker-a-20261023-c326-offline-seo-eval`. Scope: offline-only synthetic tests; no external requests, production deployment, or change to `main`.

## Why this experiment

The C326 benchmark reported 49 passing curated cases and 21,452 independent ASCII comparisons, but passing cases alone cannot measure whether the tests would detect realistic regressions. This cycle changes the question from **"does the implementation pass?"** to **"would these checks catch deliberately introduced faults?"**

## Reproducible method

`run_mutation_benchmark.py` applies 22 named, deterministic, one-at-a-time textual mutations to a copy of `research/worker_a/c318/robots_gate.py` in memory. No mutation is saved to the parser. Each mutant is checked against C326's 49 labeled fixtures; mutants surviving those checks are compared against two independent ASCII reference oracles (prefix and wildcard). A mutation is *killed* when at least one expected result differs. None of the 22 reported kills came from compilation or runtime errors.

### Before adding targeted cases

**19/22 killed (86.4%)**. Three survived:

1. `file_limit_disabled`: C326's oversize fixture also contained a path exceeding the 8,192-character rule-path guard, so removing the 500 KiB file guard still produced `unknown`. This was a *masked guard*, not evidence that the size guard was tested.
2. `url_query_dropped`: C326 tested query strings in direct paths, but did not test query reconstruction from an absolute HTTP(S) URL.
3. `prefix_score_ignores_anchor`: C326 did not contain a conflict in which the `*` or `$` syntax itself determined which matching rule had precedence.

### After adding four focused fixtures

**22/22 killed (100% of this deliberately selected mutant set)**. Four new cases isolate the missing behavior:

- Oversized `robots.txt` padded using a **comment**, keeping the rule path short.
- An absolute HTTPS URL with a query whose exact match is disallowed.
- `Disallow: /*.htm` versus `Allow: /page` on `/page.htm`.
- `Disallow: /a$` versus `Allow: /a` on `/a`.

All four pass against the unmodified parser. Locally, the C327 `unittest` suite passed **3/3 methods**, the C326 `unittest` suite passed **4/4 methods**, and the full mutation runner reported **22/22 killed**. These test methods cover multiple subcases; method counts are not individual assertion counts.

## Interpretation and limitations

- **No parser bug was fixed this cycle**: the three survivors exposed test coverage weaknesses, not known wrong outputs in the unmodified parser.
- The 100% figure is **not** a general mutation score, security proof, RFC 9309 compliance claim, or real-world crawler accuracy measure. Mutants were hand-selected, and all four new cases were designed in response to observed survivors; independent holdout mutations are needed.
- The source-level mutation runner uses in-process Python `exec` on trusted, locally defined source transformations. It must not be pointed at untrusted code or exposed as a network service.
- C326's local archive was used for local tests. Its parser's Git blob SHA (`ef238c9a4d418024cdff90b1c06566dea7626794`) matches the C326 GitHub parser. The archive's formatted C326 fixture and test files were not byte-identical to their GitHub counterparts; CI on this new branch remains unrun.

## Reproduce on this branch

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c327 python -m unittest discover -s research/worker_a/c327 -p 'test_c327*.py' -v
PYTHONPATH=research/worker_a/c318 python -m unittest discover -s research/worker_a/c326 -p 'test_c326*.py' -v
python research/worker_a/c327/run_mutation_benchmark.py
```

Next: create **holdout mutants not used to design these cases**, and cross-check interpretation against a second implementation before making any production-readiness claim. Continue favoring offline validation over network expansion without a concrete authorized use case.
