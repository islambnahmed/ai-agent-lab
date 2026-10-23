# Worker A — Cycle 319: Origin-scoped robots.txt evaluation

**Date:** 2026-10-23. **Scope:** authorized AI Agent Lab; synthetic offline tests only. No HTTP requests, crawling, or production modifications.

## Problem and change

Cycle 318's `decide(robots_text, product_token, full_url)` can evaluate any URL using the supplied robots text without checking whether that robots text belongs to the same site. A caller could inadvertently apply one site's `robots.txt` to a different host, scheme, or port, producing an unjustified allow or disallow.

Created `origin_gate.py`, a separate conservative wrapper that checks **web origin = (scheme, normalized host, effective port)**, requires source path exactly `/robots.txt`, rejects credentials, fragments, ambiguous host/port spellings and mismatched origins, and preserves explicit fetch-state uncertainty. The existing Cycle 318 parser is unchanged.

## Verification

- **31 new tests passed**, covering same-origin allow/disallow, default ports, case normalization, IPv6, cross-origin host/scheme/port, malformed authority, query preservation, and `unavailable` / `unreachable` / `not_fetched` evidence states.
- **56 prior regression tests passed** unchanged.
- **87/87 total local unit tests passed** using Python's standard-library `unittest`.
- The first run exposed an **empty-port authority** case (`https://example.test:/...`) silently treated as a default port by `urllib.parse`; added an explicit rejection, then reran all 87 successfully.
- Published source and new test blobs verified against the locally tested files: `origin_gate.py` Git blob SHA `6d9416b3b23d60f84d8613edbad1ce2151af4d60`; `test_c319_origin_scope.py` SHA `0184d1f99723e5f477a142dc3759848b411f9640`.

## Reproduction from the branch root

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c319 python -m unittest discover -s research/worker_a/c319 -p 'test*.py' -v
```

This executes the 31 new tests. The local downloadable archive also includes all 56 prior tests and the full 87-test output.

## Limitations and decisions

- This is a **decision-support gate**, not an implementation of crawler network behavior, permission to crawl, or a full RFC 9309 engine.
- `fetch_state` is explicit. `unavailable`, `unreachable`, and `not_fetched` all return `unknown`; assigning Google-specific HTTP behavior would require separate verified fetch metadata and policy.
- IDNA/Unicode hosts, trailing-dot hosts, percent-encoded authorities, and ambiguous numeric hostnames intentionally abstain rather than guess equivalence. This creates false-unknowns by design, not false permission.
- The wrapper cannot prove that supplied robots text was actually fetched from the declared source URL; that must be established by a trusted fetch layer.
- Only local fixtures were tested. No live site access, no GitHub Actions, no merge to `main`.

**Next independent experiment:** design an offline provenance record linking fetched `robots.txt` bytes to effective source URL and redirect chain, without implementing network fetches. Add adversarial examples for redirect across origins and stale cache evidence.
