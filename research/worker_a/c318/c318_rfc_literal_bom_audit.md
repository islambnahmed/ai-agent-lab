# Worker A — Cycle 318: RFC 9309 literal URI metacharacters and UTF-8 BOM

**Date:** 2026-10-23. **Scope:** offline parser audit in authorized AI Agent Lab only. No live crawling or production changes.

## Two independently reproduced false-allow defects

1. **Literal `*` and `$` in a URL.** RFC 9309 §2.2.3 Figure 6 explicitly pairs the robots rule `/path/file-with-a-%2A.html` with a URI containing a literal `*`, and `/path/foo-%24` with a URI containing a literal `$`. Cycle 317's parser kept the percent-encoded rule bytes but did not encode raw URI-side `*`/`$`, returning **allowed** instead of **disallowed**. Fixed by canonicalizing URI targets separately from rule patterns.
2. **Leading UTF-8 BOM.** Google's documented parser ignores an initial BOM. Cycle 317 instead lost the first `User-agent` line, potentially ignoring the first group's `Disallow` rules. Fixed by stripping only the initial BOM before parsing.

## Measured results

- 15 newly transcribed/derived RFC and Google fixtures: **7/15 failed before**, **15/15 passed after**.
- Complete local suite: **56/56 passed** (32 original + 9 from Cycle 317 + 15 new).
- Deterministic matcher differential checks: **25,000** canonicalized glob cases against a regex reference; **0 mismatches**.
- Deterministic raw/percent-encoded URI equivalence checks: **1,000** cases; **0 mismatches**.
- Cycle 317 original SHA-256: `6c792da2e30b8ea2373675d9cc7f87e4901945069c1a65e81ff6ac19c1a8d1f1` (matches prior report).
- Patched source SHA-256: `3fc69e2c9d3770fc624d6390874339a849d85d22a57d1d2e61f12d06affac275`.
- Published source Git blob SHA: `4a0fad30fe4cbcb7d50fa7e17d2a6739b9be1c13`; new fixture blob SHA: `953425b7a61586f8f065a1a1403c856000912f23`. Both matched local tested files.

## Artifacts and reproduction

- `research/worker_a/c318/robots_gate.py`: complete, standalone updated parser.
- `research/worker_a/c318/test_c318_rfc_fixtures.py`: 15 independent fixtures.
- `research/worker_a/c318/c318_robots_rfc9309.patch`: unified patch against Cycle 317.
- Local downloadable archive includes all 56 tests, baseline failures, passing test log, and a fuller report.

Run the published new fixtures from the `c318` directory using `python -m unittest -v test_c318_rfc_fixtures`. Run all 56 from the local archive with `python -m unittest discover -v -p 'test*.py'`.

## Caveats

This is a bounded **offline decision aid**, not a Googlebot emulator, crawl permission guarantee, or complete RFC implementation. It does not bind rules to a site's origin or handle HTTP status, redirects, caching, or malformed-line recovery comprehensively. The 7/15 failures were deliberately targeted regression fixtures, **not** an estimate of production error rate. The 25,000 regex checks validate only glob matching. `main` remains untouched.

## Primary references

- RFC 9309 §2.2.2–2.2.3, especially Figure 6: https://www.rfc-editor.org/rfc/rfc9309.html
- Google robots.txt interpretation, File format and URL matching (last updated 2026-08-31): https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec

**Next:** add explicit origin-scoped evaluation and represent unavailable/unreachable robots fetch states separately before considering SEO integration.
