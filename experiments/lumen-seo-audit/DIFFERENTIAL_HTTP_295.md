# Lumen 295 — Independent HTTP parser differential and strict wire framing

Date: 2026-10-20. Scope: authorized AI Agent Lab; synthetic loopback-only HTTP/1.1. No external sites.

## Findings
A 25-case deterministic raw-wire corpus was parsed independently with h11 0.16.0 and httptools 0.8.0. h11 marked 12 messages complete, httptools 4; completion/acceptance classifications differed on 8 cases. The Lumen conservative gate accepted 6 and rejected 19.

**Critical bug corrected locally:** Python http.client's chunk-trailer reader tolerates EOF. A chunked response ending in `1\r\na\r\n0\r\n` (without final CRLF) was accepted as a complete capture. The new StrictHTTPResponse rejects it before writing any bundle.

Other strict checks: CRLF-only status/header lines; no folded headers, control bytes, or invalid field names; 16 KiB total header budget; 4 KiB status-line budget; at most three interim 100 responses; strict chunk sizes and terminators; no chunk extensions or trailers (conservative policy).

## Tests
`python -m pytest -q test_lumen286.py test_seo_http_headers.py test_lumen293_transaction.py test_lumen294_framing.py test_lumen295_strict_headers.py` -> **87 passed** (68 prior selected tests + 19 new tests). Differential results are from a separate 25-case loopback probe. No Chromium integration or production validation.

## Limits
The corpus is synthetic and small. Extra bytes after a declared Content-Length may remain undetected because they are outside the framed message. The conservative gate is not a general HTTP standards-compliant client. HTTPS, HTTP/2/3, real WordPress pages, proxies and browser behavior are untested. Local executable code and full results are in the cycle-295 zip artifact, not asserted to be published to GitHub.

## Next
Investigate a bounded independent raw-wire capture and detect trailing bytes on locally controlled closed connections without treating connection reuse as proof of malicious framing.
