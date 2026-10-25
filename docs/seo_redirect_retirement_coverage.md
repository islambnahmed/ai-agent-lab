# Offline redirect retirement coverage (Worker A experiment)

This companion tool answers a **narrow migration question**: among URLs explicitly
designated to be retired, which have no source entry in a proposed redirect map?
It does **not** infer that every URL in a crawl needs redirecting.

## Inputs and use

Create two local UTF-8 CSV files:

```csv
url
https://example.com/retiring-page
https://example.com/another-retiring-page
```

```csv
source_url,target_url
https://example.com/retiring-page,https://example.com/new-page
```

Run offline from the repository root:

```sh
python tools/seo_redirect_retirement_coverage.py --retiring retiring.csv --map redirects.csv
python -m unittest discover -s tests -p 'test_seo_redirect_retirement_coverage.py' -v
```

Output JSON includes **physical CSV line numbers, issue types, and counts only**;
no URL values or file paths are printed. `unmapped_retiring_url` points to an
inventory line missing from redirect sources. `unlisted_redirect_source` points
to a redirect source not in the supplied retirement list (informational; it may
be legitimate). `duplicate_retiring_url` points to repeated inventory URLs.

The tool reuses the redirect-map audit's conservative URL equivalence and its
8 MiB/50,000-record input limits. It refuses a coverage conclusion when the map
has invalid/malformed rows, conflicting sources, self-redirects, or cycles.
Chains and identical duplicate sources are reported as map diagnostics, but
do not prevent source-membership checking. Blank CSV lines are skipped without
shifting physical line references. Empty-query markers remain distinct.

Exit status: **0** = coverage check completed without membership findings;
**1** = completed with findings; **2** = invalid input or blocked by map defects.
A zero exit status **does not** mean that the map is deployable or correct.

## Decision boundary

An inventory must be assembled independently from the **actual retirement
scope**, not inferred from the redirect map itself (that would make missing
sources invisible). This tool cannot establish inventory completeness, correct
destinations, deployed HTTP behavior, redirect chains' impact, indexation,
traffic recovery, or business benefit. Run it on authorized representative
migration inventories, then compare flagged line numbers against a human
reviewer before drawing field conclusions. Do not commit client URLs.
