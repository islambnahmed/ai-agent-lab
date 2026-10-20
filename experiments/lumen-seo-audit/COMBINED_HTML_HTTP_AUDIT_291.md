# Lumen 291 — Combined offline HTML + HTTP SEO audit

## Outcome — 2026-10-20
Integrated the offline Chromium DOMParser bilingual HTML SEO checker with supplied HTTP response headers. The manifest can now include per-page `headers` as ordered `[name,value]` pairs. This is a synthetic-fixture prototype, **not** live website verification.

## Verified tests
**50/50 local tests passed**: 37 existing regression tests and 13 new combined-layer tests, run with pytest and local Chromium. Tested Googlebot-scoped X-Robots-Tag noindex propagation to hreflang targets; canonical via HTTP Link alone; conflicting HTML/HTTP canonical errors; multiple HTTP canonicals; duplicate equivalent methods; malformed headers; header-injection rejection before browser startup; HTML meta robots `none`; and fail-closed `head > noscript` handling.

## Important correction
The earlier integrated auditor could mark an hreflang target healthy when the **HTTP header** said `googlebot: noindex`. It also treated `<meta name="robots" content="none">` as indexable. Both are covered in this prototype.

## Scope / limitations
Only synthetic local HTML and supplied HTTP headers were used. No WordPress site or production system was accessed. No real same-response HTML+HTTP capture is available in the authorized lab. Google indexing, redirects, response status, robots.txt, and dynamic CDN behavior remain unverified. DOMParser's scripting-mode discrepancy is handled by refusing a verdict when `<head><noscript>` is present. Local Chromium was run with no sandbox only in an isolated test environment.

## Reproduction
Run `python -m pytest -q test_lumen291_combined.py test_seo_http_headers.py test_lumen287_integration.py test_lumen286.py` on the local Lumen 291 bundle. Outcome observed: `50 passed`. Source code remains a local prototype unless a separate GitHub write is verified.

## Next
Collect an authorized paired HTML + HTTP header capture from the same URL/time and test against this prototype before considering production readiness.