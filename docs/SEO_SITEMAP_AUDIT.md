# Worker A / cycle 343 — Offline SEO sitemap QA

## Why this project

The Gold Lab's integrity stack has reached diminishing returns: earlier draft fixes establish important safeguards but do not produce new predictive evidence. This independent, reversible capability-growth experiment tests whether Worker A can deliver a practical SEO tool without contacting any sites or consuming client data. It is separate from the Gold Lab draft PR chain and makes no claim about real website rankings.

## Capability

`tools/seo_sitemap_audit.py` reads **local** XML sitemap indexes and URL sets, including `.xml.gz` children. It recursively inventories URL entries and emits deterministic JSON with issue codes for duplicate URLs (across files), off-host URLs, malformed or missing `<loc>`, malformed XML, missing child files, cycles/repeated children, future/invalid `lastmod`, oversized input, excessive entries, and unsafe XML declarations. It does not fetch remote URLs.

Index `<loc>` values are mapped to files under `--root` by URL path. The `--base-url` must be the exact HTTP(S) origin (including port if relevant); an index `<loc>` pointing outside that origin, containing traversal or an unmappable path, is reported instead of fetched. Files and symlinks resolving outside the root are rejected. Default bounds: 200 sitemaps, 50,000 entries per sitemap, and 50 MiB decompressed per sitemap. These bounds are defensive resource limits, not a complete XML security guarantee.

## Run

```bash
python3 tools/seo_sitemap_audit.py \
  --root /path/to/downloaded-sitemaps \
  --start sitemap.xml \
  --base-url https://example.com/ \
  --as-of 2026-10-24 > sitemap-audit.json

python3 -m unittest discover -s tests -p 'test_seo_sitemap_audit.py' -v
```

### Optional complete URL inventory (CSV)

The default JSON report summarizes URLs and issues but does **not** list every URL. To export every valid parsed URL entry for offline SEO QA, add:

```bash
python3 tools/seo_sitemap_audit.py \
  --root /path/to/downloaded-sitemaps \
  --base-url https://example.com/ \
  --as-of 2026-10-24 \
  --urls-csv /path/to/inventory.csv > /path/to/report.json
```

For safety, `--urls-csv` refuses destinations ending in `.xml` or `.gz`, so it cannot replace an input sitemap.

When `--urls-csv` is used, the JSON report also contains `csv_export.sha256`, `csv_export.bytes`, and `csv_export.rows`, computed from the exact exported CSV. The report records the normalized `start_sitemap` path to prevent comparing different entrypoint scopes as if they were equivalent. Save both files together for later provenance checks. These local checks detect accidental mismatch, not maliciously forged reports.

The CSV has four columns: `source_sitemap`, `normalized_url`, `lastmod`, `duplicate`. Duplicates are retained as separate rows, marked `true`, so an analyst can locate their sources. Invalid or missing URL locations remain in the JSON issues but are excluded from CSV rows. `lastmod` is the XML value, not a verified page modification time. Spreadsheet-formula-like values in the untrusted source filename and lastmod cells are prefixed with an apostrophe; import the CSV as text when using spreadsheet software. Rows stream to a temporary file in the output directory, which is replaced only after the audit finishes; **an existing destination CSV is overwritten on success**. The JSON report and its exit code retain the original meaning (0 clean, 1 issues, 2 invalid configuration/output error). This does not fetch any page or sitemap.

`--as-of` freezes future-date checks for reproducibility; omitted value uses current UTC date. The CLI exits **0** if no issues, **1** for diagnosed sitemap issues, and **2** for invalid CLI configuration. It never attempts to download sitemaps. `.xml.gz` is supported, and `<lastmod>` timestamps must have an explicit offset; a date-only value is also valid. The date is compared after UTC normalization.

### Demonstrated local cases

16 dependency-free tests cover a valid multi-file index with gzip, duplicate normalized URL, future/invalid `lastmod`, missing child and cycle, off-origin and traversal index entries, malformed XML and DOCTYPE, malformed/off-host URL entries, unexpected root, corrupt gzip, CLI exit codes and deterministic output, and configuration/sitemap-count limits. CSV export tests cover deterministic full inventories, duplicates, invalid URL exclusions and safe behavior on invalid configuration. No real customer sitemap, live HTTP response, browser, ranking data, or production deployment was used.

## Known limitations and next falsification

- **Offline inventory, not a crawl:** cannot infer HTTP status, redirects, robots/noindex, canonical tags, Google indexation, rendering, or ranking. Those require separately authorized live checks.
- URL equality is conservative (case-folded scheme/host, default-port removal, stripped fragments). It does **not** merge trailing slashes, parameter permutations, or other semantically equivalent URLs.
- A sitemap index must map to locally present files at the same URL paths; exporting only basename files without paths may trigger `missing_sitemap`.
- Large XML documents are bounded but parsed in memory; not a streaming billion-URL crawler.
- The next valuable evidence is to run against a deliberately curated, authorized local export and compare issues with a manual reviewer. Until then, no claim of SEO business outcomes is justified.

## Checkpoint

Direction changed from Gold Lab's repetitive integrity patching to an independent practical SEO QA mini-project. The Gold Lab draft PRs remain unmerged; this work must not be mistaken for Gold Lab model progress. Retain testable tool, test suite, and limitations; revise or retire if actual review utility is low.
