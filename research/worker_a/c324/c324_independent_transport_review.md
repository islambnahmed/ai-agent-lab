# Worker A — Cycle 324: independent transport review and fail-closed HTTP parser regression

Date: 2026-10-23. Authorized scope: `islambnahmed/ai-agent-lab` only. Review baseline: `sandbox/worker-a-20261023-c323-tls-loopback`.

## Decision

**Keep the offline robots evaluator as the default research tool; treat network fetching as an optional experimental component, not a production crawler capability.** The C323 TLS tests establish useful transport behavior, but do not establish trusted upstream provenance or deployment-level SSRF protection. Do not add another network feature without a concrete user-authorized use case and deployment controls.

## Independent code review

Inspected C318 `robots_gate.py`, C319 `origin_gate.py`, C320 `provenance_gate.py`, C321 `trusted_fetch_adapter.py`, C322 `pinned_https_transport.py`, and C323 integration tests. Reproduced the existing 94 tests locally before modification.

**Verified defect:** `fetch_and_decide` caught `ValueError`, `TypeError`, `OSError`, `TimeoutError`, and `ssl.SSLError`, but **not `http.client.HTTPException`**. The stdlib raises `BadStatusLine` for invalid HTTP status lines and `LineTooLong` for oversized header/status lines; neither is an `OSError`. Malformed remote HTTP could therefore escape the intended `unknown` decision boundary and raise an uncaught exception. This is a reliability/fail-closed defect; it is **not** evidence of an exploitable SSRF vulnerability.

## Reproduction and minimal fix

- Used exact C321 baseline blob SHA `9685f328fb4a2b85c9520fab35ba0f87525dd4a5` (matched local Git blob hash).
- Three offline regression tests simulate `BadStatusLine` and `LineTooLong` in the pinned path, and `BadStatusLine` in the stdlib path. Baseline: **3 errors / 3 tests**, exceptions escaped the adapter.
- Minimal change: import `http.client` and catch `http.client.HTTPException` in the existing adapter error boundary, preserving the `unknown` result and omitting any purported fetch record.
- Fixed run: **97/97 tests passed** (94 inherited + 3 new) using Python 3.13.5, OpenSSL 3.5.5. Updated C321 blob SHA: `a27bea5f6399269481ce08abca94c30d3b606e4f`.
- All new tests used mocked HTTP connections/opener and DNS. The inherited C323 integration tests used a loopback-only TLS server; no external HTTP, DNS, or crawling.

Reproduce from a flat working directory containing C318–C323 Python modules and tests, plus C324 test:

```sh
python -m unittest -q test_c324_http_fail_closed.py test_c323_tls_loopback.py test_c322_pinning.py test_c321_adapter.py test_c320_provenance.py test_c320_trust_boundary.py
```

## Compare two architectures

| Criterion | Offline trusted-record validator (C318–C320) | Live transport pipeline (C321–C323) |
| --- | --- | --- |
| External network attack surface | None | DNS, sockets, TLS, HTTP, redirects |
| Trust assumption | Upstream evidence must be independently trusted; SHA-256 alone is not provenance | Transport must be correctly configured, allowlisted and protected by deployment egress policy |
| Can independently prove source authenticity? | No | Not yet: injected transports are explicitly `test_double`; network provenance has not been audited end-to-end |
| Operational burden | Low; deterministic local fixtures | Higher; retries, DNS pinning, certificate stores, HTTP parser failures, network policy |
| Appropriate current use | **Default for offline validation/research** | Experimental integration only, disabled by default |

## Remaining issues and constraints

1. C321 still defaults to `stdlib_https_transport` if `allow_network=True` and no injected transport is supplied; that default does **not** enforce the C322 DNS/IP policy. This is documented in the source, but should be changed or hard-gated before any external use.
2. The injected pinned transport remains labeled `test_double` even when it executes real TLS; do not infer authenticated provenance from `FetchOutcome` labels.
3. No firewall/egress policy, production authorization, certificate rotation tests, HTTP interoperability corpus, or third-party review was performed.
4. A robots allow/disallow result is not permission to crawl. Failures must remain `unknown`, never be promoted to `allowed`.

## Next useful experiment

If there is a concrete SEO use case, specify its evidence provenance and success metric first. Prefer a small, independent offline corpus from authorized fetch records, with explicit unknown cases. If live fetching becomes necessary, make the pinned transport mandatory and test egress enforcement outside Python. Otherwise, park this prototype and switch to another high-value lab goal.

## Scope / persistence

Only the C321 adapter file and C324 test/report were changed on `sandbox/worker-a-20261023-c324-http-parser-failclosed`. No main merge, external network request, production deployment, or CI run was performed.
