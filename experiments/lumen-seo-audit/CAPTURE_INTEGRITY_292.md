# Lumen 292 — Offline capture-integrity gate (2026-10-20)

Status: local prototype; **not production validated**.

## Problem
The Lumen 291 HTML+HTTP auditor trusted caller-supplied body and header metadata without verifying internal capture consistency. A swapped HTML file, altered headers, redirect or 404 could be treated as a normal indexable HTML page.

## Prototype
Added optional per-page `capture` envelope: `response_url`, integer `status=200`, `content_type=text/html`, timezone-aware `captured_at`, `body_sha256`, and `headers_sha256`. `--require-provenance` refuses missing envelopes. Before browser launch, check URL equivalence, status, matching Content-Type header, decoded UTF-8 HTML digest and ordered header-list digest. Legacy manifests remain supported but report `capture_unbound`.

## Evidence
Ran `python -m pytest -q` on the bundled local prototype: **72 passed** (50 preexisting and 22 new). Tests include swapped headers, stale HTML, 301/404, non-HTML, malformed timestamps/digests and a synthetic bilingual WordPress-style page pair under Chromium.

## Caveats
No live website or genuine paired HTTP capture was tested. Digests establish local consistency **not authenticity**: the capture producer can fabricate both headers and hashes. No real redirects, crawling, Google indexing or production site changes were performed. Executable prototype is in the conversation artifact `lumen292_capture_integrity.zip`, not assumed to be on GitHub.

## Next
Develop an explicitly authorized single-transaction HTTP capture with redaction, bounded size and redirect provenance, then compare captured data with the offline auditor.