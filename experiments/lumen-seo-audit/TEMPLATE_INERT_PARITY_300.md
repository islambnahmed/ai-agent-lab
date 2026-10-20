# Lumen 300 — Inert HTML template metadata and noscript abstention

Date: 2026-10-20. Authorized AI Agent Lab; local synthetic HTML only.

## Finding
The Lumen 299 Python HTMLParser extractor interpreted SEO metadata inside `<template>` as live document metadata. Chromium DOMParser places template descendants in an inert DocumentFragment. On a 17-case adversarial synthetic corpus, **7/17** Python findings disagreed with Chromium.

## Fix and verification
- Ignore nested template contents in Python metadata extraction, without hiding live metadata following `</template>`.
- Reject `<head><noscript>` in the Python engine as scripting-mode ambiguous, matching existing browser-engine abstention.
- Same 17-case corpus after patch: **0/17** disagreements with Chromium DOMParser.
- New targeted tests: **4 passed**; combined with Lumen 299 browser parity tests: **16 passed**.
- Full pytest run printed **117 passed in 35.72s**, but the process hung in shutdown and was manually terminated; assertion success is not proof of clean teardown.
- No external pages were fetched, scanned, or modified.

## Scope
This is synthetic DOM tree-construction parity, **not** a measured false-positive rate on real sites or proof of Google's indexing decisions. Python HTMLParser remains a bounded HTML5 approximation. The browser test used no-sandbox only inside an isolated local container; do not copy that setting into untrusted production environments.

## Reproduction
The complete executable code, 17-case corpus, test suite, machine-readable results, and patch are in the Lumen 300 ZIP attachment from this cycle. Run `python -m pytest -q test_lumen300_template_inert.py test_lumen299_html5_head_parity.py` and `python measure300.py`.

## Next
Prioritize a permissioned, independently labeled real-page corpus and fix browser-process teardown before production claims.
