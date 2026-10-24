# Offline SEO redirect-map audit (independent experiment)

A small, dependency-free **preflight** checker for proposed URL redirect mappings during a site migration. It reads local CSV only and never contacts a site. It is deliberately separate from the unmerged sitemap pipeline.

## Input and run

Create a UTF-8 CSV with the exact header `source_url,target_url`, for example:

```csv
source_url,target_url
https://example.com/old,https://example.com/new
https://example.com/new,https://example.com/final
```

```sh
python tools/seo_redirect_map_audit.py --map redirects.csv
python -m unittest discover -s tests -p 'test_seo_redirect_map_audit.py' -v
```

The CLI returns JSON with row numbers, issue types, counts, and no raw URLs. Exit code **0** means no detected issue; **1** means findings; **2** means the CSV could not be read or had an invalid header. Findings include duplicate sources, self redirects, chains, multi-node cycles, and malformed URLs. A chain is any redirect whose destination is also a listed source; this can be intentional but should be reviewed.

URL matching lowercases scheme/host, treats default HTTP(S) ports as equivalent, and preserves path and query distinctions. It does **not** infer that `/a` and `/a/` are the same. Inputs are capped at 8 MiB and 50,000 rows. Credentials and URL fragments are rejected.

## Boundaries and next evidence

This is **not** a live redirect crawler. It does not validate HTTP 301/302 behavior, source coverage, redirect deployment, search-engine indexing, canonical tags, server rewrite precedence, cross-domain intent, or SEO outcomes. Duplicate source rows are reported and later duplicates are excluded from graph analysis; fix them before trusting graph results. Run against a separately authorized, representative migration map and compare with a manual reviewer before claiming field utility. No customer URLs or secrets are committed.
