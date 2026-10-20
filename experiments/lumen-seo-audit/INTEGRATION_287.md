# Lumen 287 — offline DOMParser audit integration

An end-to-end Chromium metadata integration was tested locally on 2026-10-20. Seven integration tests and nine extractor tests passed. A <template> containing an inert canonical link causes the legacy HTMLParser auditor to report CANONICAL_COUNT incorrectly; the Chromium DOMParser integration avoids that false positive. The new engine also detects hreflang targets with noindex. Failure tests reject path traversal, duplicate URLs, oversized HTML, and missing Chromium executable before any success report.

Scope: synthetic local HTML only, no live website, no production changes. Full code and tests remain in the local artifact, not in this repository until write is confirmed. Do not treat these results as Googlebot validation. Browser sandbox is enabled by default; no-sandbox is for isolated local test containers only.
