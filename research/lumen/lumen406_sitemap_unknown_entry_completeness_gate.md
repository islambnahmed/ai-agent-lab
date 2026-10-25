# Lumen 406 — Fail-closed audit for unrecognized sitemap direct children

**Date:** 2026-10-25 UTC. **Authorized scope:** `islambnahmed/ai-agent-lab`. **Status:** reversible patch committed; automated test outcome not yet independently confirmed.

## Independent finding

The composite candidate `sandbox/lumen-405-combined-review-ci` accepted a structurally incomplete XML sitemap as a clean inventory: `ElementTree.findall(NS + 'url')` selects only expected `<url>` children, while the existing diagnostic only flagged a wrong-namespace child whose local name was exactly `url`. An unexpected direct `<entry>` (same or other namespace) was silently ignored. A valid `<url>` plus a malformed `<entry><loc>...</loc></entry>` could therefore yield a clean report containing only the valid URL. The same omission applied to unexpected direct children of `<sitemapindex>`.

This matters because `tools/seo_sitemap_compare.py` considers a zero-issue report with a valid URL set and bound CSV to be complete; unknown children must not be silently omitted from completeness claims. This is a structural-integrity problem, **not** proof of any live SEO impact.

## Reversible change

- Created `sandbox/lumen-406-sitemap-completeness-review` from composite commit `838ae7e9e48b87676d5f23e1aedb404380f71369`.
- `tools/seo_sitemap_audit.py`: for direct children of both `<urlset>` and `<sitemapindex>`, issue `unexpected_entry` when a child is not the required fully qualified entry tag and its local name is not the expected entry name. Preserve existing `wrong_entry_namespace` diagnosis for wrong-namespace `url` or `sitemap` tags.
- `tests/test_seo_sitemap_audit.py`: one new regression method exercises (1) same-namespace unexpected entry next to a valid URL, (2) foreign-namespace unexpected entry next to a valid URL, and (3) unexpected sitemap-index child.
- Commits: `d95d454aa416993bdfefb62bfd39d487a3bbb299` and `ab57a0d4d171e8ffd9006ea22f0e1a2ca516cf84`.
- GitHub compare independently confirmed **2 commits ahead / 0 behind** the composite base and exactly **2 changed files** (19 test lines added; 8 tool lines added and 4 removed). Neither `main` nor peer branches were modified.

## Verification status and caveats

**Verified:** both writes and the two-file branch diff by GitHub connector. The regression tests and CI **have not been confirmed passing** in this cycle. The workflow-run connector queried by commit SHA returned no runs, but it only exposes PR-triggered runs and cannot prove that push-triggered workflows did not run. Do not claim green CI until checking the exact commit `ab57a0d4...` in GitHub Actions.

**Next checks:** run `python -m unittest discover -s tests -p 'test_seo_sitemap_audit.py' -v`, then the full offline SEO sitemap workflow on this exact branch head. If clean, review compatibility with peer PR #56, and independently inspect XML schema extension behavior before any merge.

**Scope limits:** No live crawling, production changes, external services, secrets, market forecast claims, or `main` merges. This is a review candidate only.
