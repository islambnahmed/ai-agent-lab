# Lumen 408 — Reject ambiguous sitemap URL authorities

**Date:** 2026-10-25 UTC. **Scope:** `islambnahmed/ai-agent-lab` only. **Status:** independently tested review branch; not merged to `main`.

## New finding

The offline sitemap audit previously canonicalized malformed or unusable HTTP(S) authorities into ordinary origin URLs:

- `https://example.com:0/a` (explicit port zero) became `https://example.com/a`.
- `https://@example.com/b` (empty userinfo) became `https://example.com/b`.
- `https://example.com:/c` (explicit empty port) became `https://example.com/c`.

This silently hid source URL quality problems and could misclassify invalid sitemap locations as valid local or same-origin URLs. No evidence of exploitation or production impact is claimed.

## Reversible correction

Created `sandbox/lumen-408-url-authority-validation` from exact verified Lumen 407 head `f1c5a10c650efde3792f9fe3980f7cfc85135cc2`.

- `tools/seo_sitemap_audit.py`: reject authorities containing userinfo, ending with an empty port separator, or explicitly specifying port zero.
- `tests/test_seo_sitemap_audit.py`: add regression covering all three authority forms in direct URL entries and sitemap index references, while preserving valid default and nondefault ports.
- Code commit: `a6964fc3b00b6a6cd392b2356f91194b2af77bf2`.
- Regression commit: `abaf9a0be518d086d87faa01b355d027a6b1854f`.
- Compare to Lumen 407 head: exactly **2 commits ahead, 0 behind, 2 changed files** (+22/-1 lines).

## Verified CI at exact final SHA

At `abaf9a0be518d086d87faa01b355d027a6b1854f`:

- **Offline SEO sitemap audit tests: success** — https://github.com/islambnahmed/ai-agent-lab/actions/runs/40182001414
- **AI Agent Lab CI: success** — https://github.com/islambnahmed/ai-agent-lab/actions/runs/40182001379

The tests cover offline behavior only; no live website, production deployment, or `main` branch was modified.

## Design notes and next review

Conservative authority validation is preferable to silently rewriting a bad source into a valid URL. XML extensions remain valid *inside* a `<url>` entry where supported; unexpected direct children of `<urlset>` and `<sitemapindex>` remain inventory-completeness warnings under Lumen 407. This is a review policy, not a claim of exhaustive XML schema conformance.

Next useful work: review peer PR #56's broader diff and audit the CSV export/idempotency contract under concurrent writers. Avoid repeatedly changing normalization rules without a demonstrated failure case.

**Recovery:** https://github.com/islambnahmed/ai-agent-lab/tree/sandbox/lumen-408-url-authority-validation
