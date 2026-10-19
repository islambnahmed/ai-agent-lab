# Lumen offline bilingual SEO audit (experimental)

A dependency-free Python tool for checking local Arabic/English HTML exports before launch. It reads files named by a JSON manifest and makes no network requests or changes to inputs.

Usage: `python3 audit_bilingual_seo.py pages.json --strict`

Manifest example:

```json
[
  {"url": "https://example.test/ar/", "file": "ar.html"},
  {"url": "https://example.test/en/", "file": "en.html"}
]
```

Checks: canonical count and validity, language tags, reciprocal hreflang, target language/canonical/noindex consistency, duplicate titles, and self-alternate presence. Unknown target pages are unverified, not assumed broken. Output is JSON; --strict exits 1 for errors.

Tested locally on 2026-10-19 with eight unittest cases: valid bilingual pair, missing reciprocal, noindex target, locale/canonical mismatch, duplicate title, duplicate manifest URL, path traversal, URL validation. All eight passed. The test file is retained in the local experiment package; publication of the test file was blocked.

Limitations: Not a live crawler. Does not inspect HTTP redirects, robots.txt, sitemaps, actual indexing, WordPress configuration, or search rankings. Complete reciprocity checks require all relevant pages in the manifest. No claims are made about a real website.
