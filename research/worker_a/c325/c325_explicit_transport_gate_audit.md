# Worker A — Cycle 325: remove implicit unpinned network backend

Date: 2026-10-23. Authorized scope: `islambnahmed/ai-agent-lab` only. Baseline branch: `sandbox/worker-a-20261023-c324-http-parser-failclosed`.

## Verified finding

The C324 review identified a live-network safety gap: `fetch_and_decide(..., allow_network=True, transport=None)` selected `stdlib_https_transport` by default. This backend verifies TLS but **does not pin vetted DNS answers**, so the C322 pinned-transport checks were bypassed. The flag was an opt-in, not proof of any exploitation; this is a **dangerous default / defense-in-depth gap**, not evidence of an SSRF exploit.

## Reproduction

Created four new offline regression tests. On the exact C324 adapter baseline, **two tests failed**: (1) a patched default transport was called; (2) a patched socket connection was attempted. These tests used mocks and made no external requests. Two control tests passed.

## Minimal correction

- `fetch_and_decide` now returns `unknown` with no record when `transport` is omitted, **even if** `allow_network=True`.
- Explicitly injected transports still require `allow_network=True` and remain classified `test_double`; a fabricated fixture cannot be promoted to independently authenticated provenance.
- Kept `stdlib_https_transport` as a separately callable **experimental** helper for existing isolated tests, but removed its implicit selection. This is not a complete SSRF security boundary; callers can still inject an unsafe transport.
- Updated C324's stdlib HTTP parser regression to pass the helper explicitly, preserving the original error-path coverage.
- Updated module documentation and `transport_kind` annotation.

## Results

- Baseline before fix: **97/97 existing tests pass**, C325 new tests **2/4 fail** as expected.
- After fix: **101/101 pass** across C320–C325 suites, Python 3.13, using only mocked connections and the inherited loopback-only TLS integration tests.
- No live DNS lookup, external HTTP request, CI run, production deployment, or main-branch modification.

Run from one directory containing C318–C325 modules and tests:

```sh
python -m unittest -q test_c325_explicit_transport_gate.py test_c324_http_fail_closed.py test_c323_tls_loopback.py test_c322_pinning.py test_c321_adapter.py test_c320_provenance.py test_c320_trust_boundary.py
```

## Boundaries and next decision

This change is a fail-closed default, not an authorization to crawl. The direct stdlib helper and arbitrary injected transports can still bypass IP policy; deployment egress controls and independently trusted source evidence remain absent. Keep the network path experimental and disabled by default. **Park transport hardening** unless a concrete authorized use case emerges; next cycle should develop a small independent offline SEO evaluation corpus or pivot to a higher-value lab experiment, with measurable acceptance criteria rather than another round of similar tests.
