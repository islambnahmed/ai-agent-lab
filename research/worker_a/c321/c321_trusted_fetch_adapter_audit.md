# Worker A — Cycle 321: opt-in HTTPS robots fetch adapter (offline validation)

**Date:** 2026-10-23. **Scope:** authorized AI Agent Lab only. No external HTTP requests, crawling, production changes, or changes to `main`.

## Problem
Cycle 320's `evaluate_record()` verifies consistency of caller-supplied metadata. A fabricated `RobotsFetchRecord` with matching SHA-256 can pass, so it does not establish actual network provenance.

## Implemented and published
`trusted_fetch_adapter.py` and `test_c321_adapter.py` are published on this branch. The GitHub blob SHAs match the exact files tested locally:
- `trusted_fetch_adapter.py`: `9685f328fb4a2b85c9520fab35ba0f87525dd4a5`
- `test_c321_adapter.py`: `921653ce3b0586ace796cc8ff2bf134f8d952e3e`

The adapter defaults to network disabled, requires an explicit normalized HTTPS origin allowlist, bounds redirect count/body size/timeout, suppresses environment proxies and implicit redirects, uses standard certificate verification, records same-origin redirects, generates UTC timestamps at the transport boundary, and conservatively returns `unknown` on uncertainty. Injected fixture transports are explicitly marked `test_double`, not authenticated HTTP evidence.

## Reproduce from branch root
```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c319:research/worker_a/c320:research/worker_a/c321 python -m unittest discover -s research/worker_a/c320 -p 'test_c320*.py' -q
PYTHONPATH=research/worker_a/c318:research/worker_a/c319:research/worker_a/c320:research/worker_a/c321 python -m unittest discover -s research/worker_a/c321 -p 'test_c321*.py' -q
```

**Local results:** 41/41 inherited Cycle 320 tests and 30/30 new Cycle 321 tests passed. New tests use deterministic mocks/fixtures, including malicious redirects, invalid `Location`, oversize bodies, invalid UTF-8, HTTP failures, forged fixture body and stdlib HTTPS opener construction. No live HTTP request was made. GitHub CI was not run.

## Critical limitations
1. Injected fake responses are not independently authenticated; digest consistency does not prove network origin.
2. DNS is **not IP-pinned**; DNS rebinding/SSRF remain risks without independently enforced egress policy and vetted origins. This is **not production-ready as a general fetcher**.
3. Non-200 statuses conservatively abstain. No live-origin integration or actual HTTPS redirect test yet.
4. A robots decision is not authorization to crawl.

## Next decision
Create a network-mocked HTTPError/redirect integration harness, then independently review DNS rebinding and outbound egress controls before any live traffic. Do not merge into `main` yet.
