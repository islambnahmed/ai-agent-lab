# Offline sitemap snapshot comparison (Worker A)

## Purpose

The sitemap auditor's CSV export makes a URL inventory. Comparing two snapshots helps SEO reviewers spot URL additions/removals, moved entries, modified `<lastmod>` values, and changed duplicate multiplicity. The tool does not access the network, inspect page content, or infer rankings or indexation.

## Usage

First export two inventories with `tools/seo_sitemap_audit.py --urls-csv` (from two separately saved, authorized local sitemap exports). Then run:

```bash
python3 tools/seo_sitemap_compare.py --before snapshot-1.csv --after snapshot-2.csv > sitemap-diff.json
```

Exit codes: **0** means identical URL/source/lastmod multisets, **1** means differences, **2** means invalid or unreadable input. The JSON contains sorted `added_urls`, `removed_urls`, and `changed_existing_urls` with per-source/lastmod row counts before and after. Row ordering and the `duplicate` marker's first-occurrence position are ignored; multiplicity is not. Each URL must have exactly one `duplicate=false` row (the exporter invariant), even if rows were reordered; otherwise the input is rejected with exit code 2 rather than treated as a trustworthy snapshot. Inputs must have the exact four-column exporter schema. File size and row count are bounded (64 MiB and 1,000,000 rows per CSV). No files are overwritten.

## Evidence and limitations

Five dependency-free unit tests cover additions/removals, source/lastmod and duplicate changes, order-invariance, deterministic output, and invalid input handling. Synthetic offline fixtures establish program behavior, **not** actual website SEO impact. Lastmod values are unverified sitemap claims. URL equality is exact on the exporter's `normalized_url` field; no canonical inference or HTTP fetch occurs. Snapshot differences can reflect export incompleteness or sitemap publication changes rather than actual page changes.

## Next useful validation

Compare two authorized local exports with a manual URL-level review, then evaluate whether the diff helps an SEO practitioner identify genuine sitemap regressions faster than a spreadsheet comparison. Do not treat synthetic examples as evidence of live-site performance.
