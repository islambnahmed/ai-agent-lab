# C331 — Offline CSV provenance + analyst-intent evaluation

C330 gave a robots.txt URL review queue, but its click field was unverified and a blocked URL was easy to misread as an SEO defect. C331 adds a **strict offline CSV adapter**, a required 30-calendar-day metric window, and a human-labeled *intent* evaluation. It never fetches websites, connects to Google, or auto-edits robots rules.

From repository root:

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c330 python research/worker_a/c331/offline_csv_intent_audit.py \
  --origin https://example.com --user-agent Googlebot \
  --robots-file research/worker_a/c330/example_robots.txt \
  --csv research/worker_a/c331/example_gsc_pages.csv \
  --period-start 2026-09-01 --period-end 2026-09-30 \
  --output /tmp/c331_report.json
```

Accepted CSV headers:

- Google Search Console-style pages export: `Top pages,Clicks` with optional `Impressions,CTR,Position,segment,intent_label`. The file is **not authenticated** as a GSC export.
- Manually normalized inventory: `url,organic_clicks_30d` with optional `segment,intent_label`.

`intent_label` is an optional human judgment: `intentional`, `accidental`, or `unknown`. Never infer it from robots rules or search clicks. If no labels are present, `labeled_review_precision` is **null**, not 100%. Precision is `labeled accidental disallowed / (labeled accidental disallowed + labeled intentional disallowed)`; it excludes unlabeled, unknown, and out-of-scope URLs. Coverage is reported alongside precision. No recall or actual traffic impact is estimated.

Both the property origin and the 30-day window are **user declarations**. Dates must be exactly 30 inclusive calendar days. Duplicate URL rows, ambiguous columns, non-integer clicks, invalid labels, oversized files, and invalid date windows are rejected rather than silently repaired. The underlying C330 audit remains the authority for URL origin scoping and parser decisions; it is experimental and cannot prove actual Googlebot or indexing behavior.

## Tests

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c330:research/worker_a/c331 \
  python -m unittest discover -s research/worker_a/c331 -p 'test*.py' -v
```

Only synthetic data belongs in this public repository. Do not commit client Search Console exports, proprietary URLs, or account identifiers.
