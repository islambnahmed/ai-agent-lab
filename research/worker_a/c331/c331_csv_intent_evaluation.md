# Worker A — C331: CSV provenance and manual intent precision

Date: 2026-10-23. Parent: `sandbox/worker-a-20261023-c330-seo-inventory-triage`.

## Problem and hypothesis

C330 sorted blocked/unknown URLs by user-supplied organic clicks. That is useful for triage, but a blocked page is **not** necessarily an error. A product team may deliberately disallow account or checkout URLs. Hypothesis: requiring explicit source/window metadata and measuring human-labeled accidental restrictions makes the queue more decision-useful than reporting parser pass rates or assuming all blocked URLs require remediation.

## Implemented

- Offline, strict CSV ingestion of Google Search Console-style `Top pages,Clicks` or normalized `url,organic_clicks_30d`; unknown/ambiguous columns fail closed.
- Explicit, exactly 30-calendar-day inclusive metric window; provenance marks source, dates, origin, and labels as user-supplied and **not authenticated**.
- Explicit manual `intent_label` values (`intentional`, `accidental`, `unknown`). Labels never change the parser's crawl-policy result.
- Precision among **known-intent, disallowed** URLs and separate known-intent coverage. Unknown intent is not counted as a correct recommendation; out-of-scope is excluded.
- Input guards for invalid dates, non-integer clicks, duplicate URLs, CSV width, UTF-8, maximum file size, and 50,000-row limit. No HTTP, DNS, OAuth, credentials, or live exports.

## Reproducible local results

Using C330 and C318 modules from the previously published branch and synthetic C331 data:

```bash
export PYTHONPATH=research/worker_a/c318:research/worker_a/c330:research/worker_a/c331
python -m unittest discover -s research/worker_a/c330 -p 'test*.py' -q
python -m unittest discover -s research/worker_a/c331 -p 'test*.py' -q
python research/worker_a/c331/offline_csv_intent_audit.py --origin https://example.com \
  --user-agent Googlebot --robots-file research/worker_a/c330/example_robots.txt \
  --csv research/worker_a/c331/example_gsc_pages.csv \
  --period-start 2026-09-01 --period-end 2026-09-30 --output /tmp/c331_report.json
```

Observed: **9/9 C330 tests and 10/10 C331 tests passed** locally. The CLI produced 7 rows: 2 allowed, 3 disallowed, 1 unknown, 1 out-of-scope. Among 3 disallowed rows, 2 had known analyst intent: 1 accidental and 1 intentional. Thus **labeled review precision = 50% with known-intent coverage = 66.7%**. One disallowed row remained unlabeled. The out-of-scope accidental label and invalid URL accidental label were correctly excluded from precision. These are illustrative synthetic labels, not an external benchmark or verified SEO outcome.

## Limits and next experiment

- The CSV may resemble a GSC export but is not validated against Google Search Console; supplied clicks are historical context, **not lost traffic**.
- The period is declared, not verified; source URLs and labels are not independently authenticated.
- A human label can be wrong; this evaluation is not independent ground truth. There is no precision estimate for unlabeled populations, no recall estimate, and no production-readiness claim.
- Parser behavior is inherited from experimental C318/C330; no network checks or CI runs were performed.
- Next: blinded review by independent analysts using only authorized synthetic or public data, compare queue ranking against a simple baseline, and report inter-rater agreement and label coverage before claiming improved decision quality.
