# Offline sitemap change review queue (Worker A)

## Why

A raw sitemap snapshot diff is useful but not immediately actionable. This small dependency-free utility converts the existing diff JSON into a deterministic CSV review queue. It **does not** decide that a page was deleted, indexed, deindexed, redirected, or ranked differently. All entries are **suggestions for human review**, not confirmed SEO incidents.

## Workflow

First save two authorized offline sitemap exports and audit them using `tools/seo_sitemap_audit.py --urls-csv`. Keep each corresponding JSON audit report. Compare them with `tools/seo_sitemap_compare.py` using both `--before-report` and `--after-report` when available.

The comparator returns exit code **1** when differences exist; that is expected. Capture its JSON even when exit code is 1:

```bash
python3 tools/seo_sitemap_compare.py \
  --before snapshot-1.csv --before-report snapshot-1.json \
  --after snapshot-2.csv --after-report snapshot-2.json > sitemap-diff.json
python3 tools/seo_sitemap_triage.py --diff sitemap-diff.json > review-queue.csv
```

The queue columns are `priority,change,url,review_action,evidence,rows_before,rows_after`. Blank row counts mean the diff format does not disclose that multiplicity for a wholly added/removed URL; **do not interpret a blank as one**.

- **P1**: URL disappeared from the later *offline inventory*. Check whether that was intentional, and review relevant redirect behavior independently.
- **P2**: a URL's sitemap source placement or duplicate row count changed. Check configuration and coverage.
- **P3**: URL added, or only its claimed lastmod / metadata distribution changed. Review as appropriate.

Priorities are heuristic *review order*, not measured SEO risk or business impact. The evidence field is `local_csv_sha_checked` only when the comparator reports matching local audit/CSV SHA-256 metadata; this does not authenticate the source website or capture time. Otherwise it is `csv_only_unverified`. The utility never silently upgrades evidence quality. It does not access the network, crawl sites, inspect content, check redirects, or use client data.

## Evidence

Seven local unit/CLI regressions cover realistic-shaped mixed changes, review priority ordering, changed multiplicity, provenance preservation, invalid data, deterministic ordering and CSV output. They use synthetic `example.com` fixtures and the comparator's actual `compare()` output; they do not establish live-site utility. A useful next evaluation is a blinded manual review of two independently saved, explicitly authorized real sitemap exports, comparing triage usefulness and false alarms against spreadsheet review.
