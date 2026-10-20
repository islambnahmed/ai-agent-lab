# Lumen 283 — HTML parser candidate benchmark (2026-10-20)

## Result
On 28 synthetic offline HTML fixtures, compared to Chromium 144.0.7559.96 DOM with document JavaScript enabled:
- Legacy Python HTMLParser extractor: **12/28 match**, 16 mismatches.
- lxml.html candidate: **17/28 match**, 11 mismatches.
- Chromium: reference DOM, not an SEO or Googlebot oracle.
- 3/28 fixtures changed DOM metadata when document JavaScript was disabled (all involved noscript).

Indicative timing for 28 fixtures: HTMLParser 0.59ms, lxml 1.58ms median in-process extraction; Chromium 190.67ms for loading/evaluating 28 fixtures (excludes startup). These are not directly comparable throughput measurements.

## Decision
Do **not** promote lxml.html as a standards-conformant HTML5 replacement. It still disagrees with Chromium for metadata after head closure, template, noscript, and self-closing head syntax. A real HTML5 parser (html5lib or parse5) remains an untested candidate; html5lib installation was blocked by unavailable package network.

A local Chromium static-HTML extractor prototype was built with document JavaScript disabled, network requests blocked, manifest path containment, and a 2MB/file limit. Eight local unit tests passed. Chromium is a DOM reference, not evidence of indexing or SEO correctness. The prototype uses --no-sandbox in this container; do not run untrusted HTML outside a suitably isolated environment.

## Limitations
Synthetic fixtures, not sampled production HTML; no real sites, Googlebot, HTTP headers, robots.txt, or production modifications. Mismatch rates cannot be extrapolated to the web. The browser JS-on reference and JS-off static extractor intentionally target different DOM semantics for noscript.

## Next
Evaluate a true HTML5 offline parser against Chromium when an approved dependency is available; then validate on held-out user-authorized HTML snapshots. Keep current extractor marked approximate. Gold data recovery remains unresolved.

Local artifact: lumen283_parser_candidates.zip (benchmark script, JSON results, static Chromium extractor, 8 tests, original extractor).
