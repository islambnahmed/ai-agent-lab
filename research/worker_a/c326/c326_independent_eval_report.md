# Worker A — C326: independent offline SEO benchmark and anchor validation

Date: 2026-10-23. Base: `sandbox/worker-a-20261023-c325-explicit-transport`. All activity is inside the authorized repository, offline only. No crawl, external HTTP, production deployment, GitHub CI, or change to `main`.

## Direction change

After six transport-focused cycles, park network hardening and evaluate the decision aid directly. This branch contains 49 synthetic labeled robots.txt cases, an independent prefix oracle (13,950 combinations), an independent ASCII wildcard oracle (7,502 combinations), and 90 BOM/CRLF/rule-order invariance checks.

Case breakdown: basic (13), user-agent groups (10), wildcard (8), encoding (8), conservative abstention (10). Reference points: [RFC 9309](https://www.rfc-editor.org/rfc/rfc9309.html) and [Google robots.txt interpretation](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec). The `unknown` labels for malformed inputs are **local policy**, not a claim about every crawler.

## New regression found

The previous parser silently returned `allowed` for unsupported repeated terminal anchors `Disallow: /a$$` and `Disallow: /$$`. The check `'$' in value.rstrip('$')` accidentally stripped *all* trailing anchors before validation. Two new cases failed on the C325 baseline.

On this isolated C326 branch, the C318 parser's condition was changed to `'$' in value[:-1]`, so any dollar sign before the final position causes a conservative `unknown` result. This is a fail-closed **input-policy correction**, not a demonstrated real-world search-engine security exploit.

## Local verification

- Before patch: 47/49 curated cases pass; 2 repeated-anchor cases fail.
- After patch: **49/49** curated cases pass.
- **13,950/13,950** independent ASCII prefix combinations pass.
- **7,502/7,502** independent ASCII wildcard combinations pass.
- **90/90** deterministic invariance comparisons pass.
- **105/105** local unittest methods pass: 101 inherited C320–C325 tests and 4 new C326 test methods. Each new method checks many subcases.
- The patched parser Git blob SHA is `ef238c9a4d418024cdff90b1c06566dea7626794`, matching the locally tested patched source.

Run from repository root:

```bash
PYTHONPATH=research/worker_a/c318 python -m unittest discover -s research/worker_a/c326 -p 'test_c326*.py' -v
```

The inherited 101-test regression was run locally using the previous C325 archive's flat Python module layout and the patched parser; it was **not** executed on GitHub CI.

## Limits and next experiment

Synthetic data cannot establish population-level false-allow rates or full RFC conformance. The independent oracles cover narrow ASCII sublanguages; no live site, fetch, DNS, or TLS behavior is tested. Next: mutation-test the benchmark and measure which known parser faults it detects, rather than growing the network stack without a concrete authorized use case.
