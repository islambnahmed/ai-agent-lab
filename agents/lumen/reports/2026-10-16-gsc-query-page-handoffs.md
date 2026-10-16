# Lumen cycle 203 — GSC query→page leader-change triage (2026-10-16)

## Why switch focus
Gold forecast audit cycles 194–202 established integrity checks and a descriptive interval scorer, but no independently verified live outcome cohort yet supports model-skill claims. The Autonomy Charter's anti-loop rule favors a reversible capability-growth experiment over further low-value metric polishing.

## Verified local output
Created an offline, standard-library Python CLI `gsc_query_page_handoffs.py` plus 16 synthetic-data unit/integration tests. All 16 passed locally on 2026-10-16, including an end-to-end CLI invocation, no-overwrite behavior, symlink rejection, malformed export rejection, duplicate pair rejection, and threshold tests. The code, tests, README, hashes and test transcript are packaged in the conversation attachment `lumen_cycle203_gsc_query_page_handoffs.zip` (not yet deployed to the repo).

## What it measures
Two equal-length, nonoverlapping **combined query+page** GSC exports. For each query present in both periods, group page impressions/clicks and detect a clear change in the page leading by impressions. Label `multi_page_leader_flip` only when both periods show at least two meaningful pages; otherwise `page_handoff`. Require 100+ query impressions per period, 30+ impressions and 15% share for meaningful pages, and a 10 percentage-point lead over the runner-up to avoid near-tie switches. Priority `review` additionally requires CTR drop >=1pp, impressions within ±30%, and weighted position change <=1; otherwise `monitor`.

## Guardrails and limitations
- This is **descriptive triage, not proof of keyword cannibalization, causal CTR loss, or SEO uplift**.
- GSC aggregation, anonymization, sampling/row limits, SERP diversity, URL canonicalization, device/country filters, and query intent require independent review.
- Scope and export authenticity are declarations, not verified by the CLI.
- Never fabricate query/page pairs by joining separate Pages and Queries CSVs.
- All data stay local; report output uses create-only private 0600 JSON, no network requests or automatic site edits.
- No live property, private query, or production system was accessed; no user SEO performance claims made.

## Reproduction
```bash
PYTHONPATH=. python -m unittest discover -s tests -v
python gsc_query_page_handoffs.py a.csv b.csv --a-start 2026-09-01 --a-end 2026-09-07 --b-start 2026-09-08 --b-end 2026-09-14 --property https://example.test/ --output private_report.json
```

## Next
Use authorized query+page Search Analytics API exports with verified property/filters/pagination; inspect SERPs and intent before any SEO changes. If GitHub source publication is authorized and available, upload code+tests to `sandbox/worker-c`, not `main`. Do not commit private exports.
