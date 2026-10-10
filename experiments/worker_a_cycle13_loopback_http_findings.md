# Worker A cycle 13 — Loopback HTTP evidence (2026-10-10)

Executed a real ephemeral 127.0.0.1 HTTP server and a bounded HEAD-only collector. No external hosts contacted. The collector rejects non-loopback origins, skips cross-origin links, never follows redirects, never fetches bodies, and treats HEAD 405/501 as unknown rather than broken.

**Tests:** 29/29 passed locally (6 new integration tests + 23 prior regressions), `python -m unittest -v test_worker_a_loopback_http_probe.py test_worker_a_site_audit_evidence_v2.py`, 2.704 s. Independent oracle covered 200/201/204/301/302/404/410/503/405/501 and an end-to-end feed into the offline audit. 404/410 -> broken, 301/302 -> redirect, 503 -> server error, HEAD unsupported -> unknown, 200 -> no finding.

**Reproducibility:** The exact source and test output were bundled as `worker_a_cycle13_bundle.zip` in the conversation artifact, NOT committed here. This report alone does not make the test reproducible from GitHub. Do not claim a repository code artifact without verifying a separate upload.

**Limits:** Only synthetic loopback fixture, no live site, no autonomous agent. HEAD differs from GET on some servers. Next: tamper-evident provenance and independent replay oracle.
