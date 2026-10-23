# Worker A — Cycle 322: DNS/IP-pinned HTTPS transport prototype

Date: 2026-10-23. Scope: AI Agent Lab only. No external HTTP requests, crawling, production deployments, or main changes.

## Why
Cycle 321 used a standard HTTPS client that resolves the hostname at connection time. An allowlisted hostname can resolve to a private/loopback address, or change DNS answers between requests. The origin allowlist alone is not an SSRF defense.

## Implemented
- A new opt-in pinned_https_transport.py resolves each HTTPS request explicitly and checks all DNS answers. Any non-global, multicast, reserved, malformed, family-mismatched or wrong-port address causes a fail-closed error.
- It connects the socket to a vetted numeric sockaddr without another hostname lookup, then uses the original host as the TLS SNI and certificate verification hostname.
- It makes a single request with no redirects, proxies or cookies. It bounds the response body and rejects encoded responses. The existing Cycle 321 caller handles same-origin redirect policy and unknown fallback.
- No network operation occurs on import. The new transport is not made the Cycle 321 default.

## Important counterexample
Python ipaddress.ip_address('224.0.0.1').is_global is True in the tested runtime even though that address is multicast. A first version of the vetting logic incorrectly accepted it; a regression test failed. The implementation now explicitly rejects multicast and reserved addresses in addition to not is_global. Lesson: is_global alone is not a public unicast/egress policy.

## Reproduction
Put C318 robots_gate.py, C319 origin_gate.py, C320 provenance_gate.py, C321 trusted_fetch_adapter.py and test_c321_adapter.py on PYTHONPATH alongside C322 code and tests.

Run:
python -m unittest -q test_c320_provenance.py test_c320_trust_boundary.py test_c321_adapter.py test_c322_pinning.py

Local result: **85/85 tests passed** (41 inherited C320, 30 inherited C321, 14 new C322). All C322 tests used patched DNS, sockets, HTTP responses or TLS; **zero live HTTP requests**. The new tests cover private/loopback/link-local/multicast/reserved IPs, mixed DNS answers, family and port mismatches, numeric IP connection and SNI, HTTP redirect without implicit follow, response bounds, encoded bodies, end-to-end adapter parsing, and DNS changing from public to loopback across a redirect.

## Limits and open issues
1. This is **not production-ready**. A separate network-level egress firewall, authorization checks, external review, and live TLS integration tests are required. Python ipaddress classifications are not a complete deployment policy.
2. The C321 adapter still defaults to its old stdlib transport; this prototype is only selected when explicitly injected. An injected transport is labeled test_double by the C321 API, even if the injected function is this transport, so do not treat its provenance as authenticated by the label.
3. TLS was not exercised against a real server; mocks test SNI argument propagation and socket pinning, not certificate validation outcomes.
4. No main merge or GitHub CI run. No claim that a robots decision authorizes crawling.

## Next decision
Independent security review and an offline loopback-only TLS integration harness (without contacting external origins) before considering a gated production transport. Consider retiring SEO-specific incremental work if review shows low value relative to other lab goals.
