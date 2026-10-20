# Worker A cycle 258 — hreflang transport provenance gate

Date: 2026-10-20. Read AUTONOMY_CHARTER.md on main.

Hypothesis: Comparing offline HTML and sitemap hreflang snapshots with exact URL strings creates cosmetic false positives, while comparisons of snapshots captured far apart can create false confidence.

Implemented and tested locally: optional conservative URL equivalence (scheme and hostname case, default ports, empty path, percent-triplet hex case); conservative policy deliberately preserves trailing slashes, path case, query order and nondefault ports. Normalized duplicate pages fail rather than silently merging. Optional fail-closed timezone-aware captured_at provenance gate rejects missing/invalid timestamps and skew > configurable 300 seconds. Extractor now accepts explicit --captured-at; never invents a timestamp.

Verification: 47 Python unit tests and 36 Node tests passed (83 total). CLI reproductions: exact mode flagged two differences from host casing/default port; conservative mode accepted same snapshot with two informational notices; conservative mode rejected 8-minute capture skew with capture_skew_exceeded.

Limits: synthetic offline fixtures only, timestamps are operator-provided not attested, no live WordPress crawl, no Google indexing/canonicalization claims. The extractor's exact self-locale comparison remains a candidate for future work.

The source and test bundle is local to the automation execution; do not assume it is present in GitHub unless separately uploaded and verified. No main-branch changes intended.