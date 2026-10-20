# Lumen 286 — Inert Chromium DOMParser benchmark (2026-10-20)

**Scope:** AI Agent Lab synthetic offline HTML. No production changes.

## Finding
Rather than patching html5lib's handling of `<template>` inside `<head>`, tested browser-native `DOMParser.parseFromString(markup, 'text/html')` in an inert document.

- **428/428** metadata results matched Chromium 144.0.7559.96 live static DOM on the same synthetic corpus (28+40+180+180 cases). Same-engine agreement is not independent validation of SEO correctness.
- A 10-case adversarial inert-parse smoke test (meta refresh, scripts, onerror, iframe, preload, data URLs, base URL) produced **0 observed network requests, 0 navigations, 0 page errors**.
- Single-process 428-case timing: inert DOMParser **0.616 s** vs `page.set_content` **2.144 s** (~3.48× faster); startup excluded and only one run.
- `tinyhtml5` 2.1.0, despite being a public library, showed the **same 15/428 mismatches** as vendored html5lib on this corpus.
- Reusable inert extractor passed **9/9** local tests including meta refresh, template-in-head, script inertness, input bounds and noscript.

## Limits and decision
Only synthetic offline HTML; no live sites, Googlebot, indexing or ranking. Network blocking and JS-disabled context were enabled; `--no-sandbox` was used only in isolated root tests. The reusable extractor defaults to the Chromium sandbox and requires an explicit unsafe override for that testing configuration. Inert DOMParser is not an HTML sanitizer or a guarantee that all third-party HTML cannot initiate requests. Browser crashes/timeouts and real-world fixtures remain untested.

**Decision:** promote DOMParser to a **prototype candidate**, not production. Next: authorized real-world holdout and threat-model review. Local reproducibility bundle: `lumen286_inert_domparser.zip` (SHA256 `f2c62432b6614800a1458052f49dd11d6d0fccee8a6994280a9b2ec96cfb1913`).
