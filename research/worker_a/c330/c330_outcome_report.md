# Worker A — C330: turn parser correctness into an actionable SEO triage artifact

Date: 2026-10-23. Parent branch: `sandbox/worker-a-20261023-c329-published-reference`.

## Decision and motivation

The C327–C329 cycle sequence measured correctness and mutation detection, but did not demonstrate a practical SEO analyst workflow. Instead of continuing to optimize a synthetic parser score, this cycle built a **local, origin-scoped inventory triage CLI**. It reads a previously saved robots file and a synthetic URL inventory, classifies paths, segments findings, and orders manual-review candidates using user-provided historical organic clicks. No crawler, DNS, live site, or Google Search Console connection is claimed.

## Distinct capability added

- Origin-bound input validation prevents mistakenly applying one site's robots rules to URLs on other origins. Scheme and effective port are part of the origin.
- Invalid URLs and malformed robots rules result in `unknown` rather than a guessed permission.
- `out_of_scope` is separate from `unknown` and **excluded** from flagged click totals; otherwise external URLs could distort prioritization.
- Duplicate in-scope targets are ignored after the first occurrence, avoiding inflated totals; caveat: first row wins.
- Results include per-URL matched rule/reason, counts by segment, and a click-sorted review queue. Clicks are **context for review only**, not a claim about traffic loss.
- No network transport or new dependency was introduced. Original C318 parser was not changed.

## Reproducible local evidence

Commands from repo root:

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c330 python -m unittest discover -s research/worker_a/c330 -p 'test*.py' -v
PYTHONPATH=research/worker_a/c318:research/worker_a/c329 python -m unittest discover -s research/worker_a/c329 -p 'test*.py' -v
PYTHONPATH=research/worker_a/c318 python research/worker_a/c329/run_c329_ascii_differential.py
PYTHONPATH=research/worker_a/c318 python research/worker_a/c330/offline_robots_inventory_audit.py --origin https://example.com --user-agent Googlebot --robots-file research/worker_a/c330/example_robots.txt --inventory research/worker_a/c330/example_inventory.json --output /tmp/c330_report.json
```

Observed locally on the C329 packaged parser and C330 files:

- **9/9** new `unittest` methods passed, including 300 deterministic cross-origin URL examples, CLI smoke test, origin validation, duplicates, malformed URL, malformed robots, and click-field validation.
- **2/2** available C329 regression methods passed; the C329 ASCII differential runner matched **10,000/10,000** comparisons in its narrow documented scope.
- Synthetic 5-row inventory: **2 allowed**, **1 disallowed**, **1 unknown**, **1 out of scope**. Two review candidates, with **15 historical clicks** supplied as prioritization context (12 + 3); 50 clicks from the out-of-scope row correctly excluded.
- Early test failure revealed a real implementation bug: port `0` was silently treated as default by `p.port or default`. Fixed using explicit `is not None`, then reran the suite successfully.
- A test expectation was temporarily mismatched during separation of `out_of_scope`; corrected and reran tests. These intermediate failures are not counted as successful runs.

## Decision-quality and limits

This is a *working offline triage prototype* for synthetic data, not an SEO audit of a real domain. `robots.txt` only constrains crawling; a blocked URL may be correctly protected, and an allowed URL may still not be indexed. Never auto-edit robots directives from this report. No GitHub CI or external HTTP tests were performed.

**Next useful experiment:** add an offline CSV import with explicit data-provenance fields (export date, property, metric), compare the review queue to independently labeled *intentional vs accidental* restrictions, and measure analyst precision rather than parser-only accuracy. Use synthetic or authorized non-sensitive data only.
