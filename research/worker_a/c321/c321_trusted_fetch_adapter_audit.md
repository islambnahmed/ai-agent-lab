# Worker A — Cycle 321: opt-in HTTPS robots fetch adapter (offline validation)

**Date:** 2026-10-23. **Scope:** AI Agent Lab only. No external HTTP requests, no crawling, no production changes, and no changes to `main`.

## Motivation
Cycle 320's `evaluate_record()` verified only caller-supplied metadata consistency: a fabricated `RobotsFetchRecord` with a matching SHA-256 digest passed. A trusted transport must collect bytes, redirect evidence and timestamps itself rather than trusting records handed to it.

## Deliverable
Prepared and locally tested `trusted_fetch_adapter.py` and `test_c321_adapter.py` (local bundle, not yet present on this GitHub branch). The adapter provides:
- Explicit network opt-in and exact HTTPS origin allowlist.
- Bounded redirects, response size, and timeouts; fail-closed `unknown` outcomes.
- Stdlib TLS certificate verification, no inherited environment proxy, no automatic redirect following.
- Redirect-chain validation and UTC timestamp generation at the adapter boundary.
- Clear `test_double` marking for injected fake responses, which are not network authentication.

## Local verification
**41/41 inherited Cycle 320 tests and 30/30 new Cycle 321 tests passed.** All new tests used deterministic fixtures/mocks; no live network requests were made.

## Critical limitations
1. A test double can fabricate data. SHA-256 consistency does not establish network provenance.
2. DNS resolution is **not IP-pinned**. DNS rebinding and SSRF remain possible without independently enforced network egress restrictions and vetted origins. Do not deploy as a general URL fetcher.
3. No live-origin integration or GitHub CI test has been performed. Non-200 responses conservatively abstain.
4. A robots.txt decision is not authorization to crawl.

## Next step
Publish the exact locally tested code and tests if permitted, add an HTTPError/redirect transport integration harness, and independently review egress/DNS restrictions before enabling live network use. Do not merge into main yet.
