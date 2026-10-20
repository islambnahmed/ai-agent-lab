# Lumen 297 — SEO verdict precision: optional hints are not errors

Date: 2026-10-20. Authorized AI Agent Lab only. No production site accessed or modified.

## Finding
The Lumen 296 auditor emitted `CANONICAL_COUNT` errors and `MISSING_SELF_HREFLANG` warnings on an ordinary page with no explicit canonical or hreflang markup. It also labeled a hreflang target as confirmed noncanonical merely because `rel=canonical` was absent. These are ungrounded SEO verdicts: Google can select canonical URLs without a declared hint, and hreflang self-reference checks apply when localized variants are declared.

Official documentation:
- https://developers.google.com/search/docs/crawling-indexing/canonicalization
- https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- https://developers.google.com/search/docs/specialty/international/localized-versions

## Change
- Do not emit `CANONICAL_COUNT` for an absent canonical; retain errors for duplicate HTML canonicals and malformed attempted HTTP canonicals.
- Do not emit `MISSING_SELF_HREFLANG` when hreflang was never attempted; retain warning for incomplete or malformed attempted declarations.
- Do not emit `HREFLANG_NONCANONICAL` when the target has no explicit canonical; retain it for a conflicting explicit canonical.
- Remain an offline hints validator, not a Google-selected canonical oracle.

## Controlled A/B verification
- Seven new synthetic precision cases against the unmodified 296 code: 4 failed, 3 passed.
- Same seven after patch: 7 passed.
- Entire locally bundled suite after patch: **89 passed**, zero failed (Python and Chromium tests where available).
- An existing malformed-Link regression initially failed; implementation was corrected to preserve an error for an explicit malformed canonical attempt.
- These 89 tests are the suite bundled in the local 296 artifact plus seven new cases; this does not claim all tests from other branches/artifacts.

## Limitations
Synthetic fixtures only. No production website or Search Console verification. Self-referencing canonical remains a useful recommendation even when absent markup is not a proven error. Malformed-HTTP canonical detection uses a heuristic regex requiring future fuzz testing. Site-wide missing hreflang cannot be inferred from unrelated manifest URLs without a declared translation mapping.

## Reproduction
Apply `LUMEN297_PRECISION.patch` to `audit_bilingual_seo_integrated.py` from the Lumen 296 bundle; add `test_lumen297_seo_precision.py`; run `python -m pytest -q`. The conversation zip includes a runnable bundle and test cases. No remote fetch is performed by tests.

## Next
Use permissioned real captures and manually labeled gold standards; separate actionable errors from optional SEO recommendations. Prioritize measured false-positive rates over test-count growth.
