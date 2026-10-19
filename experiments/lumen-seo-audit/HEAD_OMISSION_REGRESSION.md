# Lumen 281 — implicit </head> regression (2026-10-20)

Scope: offline SEO audit experiment only. No production changes.

## Reproducible counterexample
```html
<html lang="en"><head><title>English</title><link rel="canonical" href="https://example.test/en/"><body><link rel="alternate" hreflang="en" href="https://example.test/en/"></body></html>
```
HTML permits omitting `</head>`; the explicit `<body>` closes the head. Python `html.parser.HTMLParser` does not implement that implied closure. The 2026-10-20 audit's `Extract` class leaves `in_head=True`, so it accepts a body `hreflang` as a head declaration, incorrectly reporting no `LINK_OUTSIDE_HEAD` error.

## Local verification
- Baseline: 19 existing tests pass; 2 of 3 new regression tests fail.
- Patch: when `handle_starttag` sees `body`, set `in_head=False` and `seen_body=True`; reject any subsequent `head` reopening.
- Patched result: 22/22 tests pass, including healthy bilingual fixture with 0 errors.
- The local full patch/test bundle is separate; this note is NOT a claim that the patch was published.

## Standards
WHATWG HTML syntax: https://html.spec.whatwg.org/multipage/syntax.html#optional-tags

## Boundaries
This audit is manifest-only; it is not a browser-grade HTML5 parser and does not validate live indexing. Next useful experiment: browser-DOM differential test on authorized local fixtures.
