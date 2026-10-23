# Worker A — Cycle 323: offline TLS integration evidence

Date: 2026-10-23. Scope: `islambnahmed/ai-agent-lab` only. No external HTTP, crawling, deployments, credentials, or changes to `main`.

## Objective
Cycle 322 tested DNS/IP pinning and TLS hostname arguments with mocks, but not a real TLS handshake. This cycle tested the real Python HTTPS stack against a **loopback-only, ephemeral local TLS server**.

## Experiment
Added `test_c323_tls_loopback.py`. It creates a one-day self-signed certificate with SAN `DNS:lab.test` using local OpenSSL, stores the private key only in a temporary directory, binds the HTTPS server exclusively to `127.0.0.1` on a random port, and deletes the certificate/key after tests. No keys are committed.

Only in the test, `vetted_addresses()` is mocked to return the local numeric socket address and the SSL trust store is augmented with the ephemeral certificate. The actual production `vetted_addresses()` is separately tested to reject loopback. The override does not weaken the production policy.

Real TCP/TLS and HTTP paths tested: trusted hostname, hostname mismatch, untrusted certificate, no implicit redirect following, declared oversize, chunked oversize, encoded body rejection, loopback policy rejection, and end-to-end adapter decision.

## Reproduction
From a working directory containing C320–C322 modules/tests plus C323 test:

```sh
python -m unittest -q test_c323_tls_loopback.py test_c322_pinning.py test_c321_adapter.py test_c320_provenance.py test_c320_trust_boundary.py
```

**94 tests passed** locally: 9 new real-TLS tests plus 85 inherited. OpenSSL 3.5.5. An initial test used `http_status` instead of `status_code`; this test-authoring mistake was fixed and all tests rerun.

## Evidence boundaries
The tested transport completed a real TLS handshake to a pinned numeric loopback address while verifying `lab.test`. Wrong hostname and untrusted certificates failed with `SSLCertVerificationError`. Redirects were not silently followed; body bounds were enforced. The adapter returned `disallowed` using the local robots file.

**Not established:** production readiness, external TLS interoperability, SSRF resistance beyond the tested DNS policy, network firewall enforcement, remote CA behavior, or authenticated provenance labels. The adapter still calls injected transports `test_double`. No external HTTP requests were made, and a robots decision is not authorization to crawl.

## Next decision
Stop expanding this SEO-specific prototype without a concrete use case. Independently review the trust boundary and compare with the simpler option of offline robots validation from upstream trusted fetch records.