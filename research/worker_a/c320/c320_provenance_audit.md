# Worker A — Cycle 320: Offline robots.txt fetch-evidence consistency gate

**Date:** 2026-10-23. **Scope:** authorized AI Agent Lab, offline synthetic fixtures only. No HTTP requests, crawling, or production changes.

## Problem

Cycle 319 checked whether the declared `/robots.txt` URL and target URL shared an origin, but could not connect the supplied body to a recorded fetch. A stale, altered, or misrouted response could be treated as authoritative if a caller supplied a plausible URL.

## Reversible implementation

Added `provenance_gate.py` with a typed `RobotsFetchRecord`, `RedirectHop`, and `evaluate_record()` wrapper around the existing Cycle 319 `decide_scoped()` function. The gate requires:

- A root `/robots.txt` request on the target origin; exact final destination and contiguous redirect hops; only 301/302/303/307/308 hops; at most 5 by default.
- Every redirect destination on the original origin (deliberately conservative; some legitimate cross-origin redirects are therefore UNKNOWN).
- Final status exactly HTTP 200, exact response bytes, lowercase SHA-256 matching those bytes, and strict UTF-8 decoding.
- Timezone-aware fetch and evaluation timestamps; a non-future record within the configured freshness window (24 hours by default).
- Fail-closed `unknown` for malformed, cross-origin, broken-chain, stale, altered, or ambiguous evidence.

## Verification and critical limitation

**41/41 local tests passed** (40 main regression tests + 1 explicit trust-boundary counterexample), using Python standard-library `unittest` and local functional mirrors of the Cycle 318/319 dependencies. The three new GitHub source/test blobs were compared with the locally tested files by Git blob SHA:

- `provenance_gate.py`: `fa54aaaa8c45a3643b2cc59c573ca76925ca1134`
- `test_c320_provenance.py`: `fb099036ef90f590dbcd507574fb281ef8bb89fe`
- `test_c320_trust_boundary.py`: `f790b2f57597ab0bc9327904f4c16ec88c04439e`

**Important negative result:** A completely fabricated body and fabricated URL can pass if the caller supplies a matching SHA-256 digest and a recent timestamp. A digest proves only consistency between supplied bytes and digest; it does not authenticate the claimed HTTP origin or timestamp. The `evidence_consistent` flag is *not* a network provenance attestation. The negative test demonstrates this explicitly. Never treat this wrapper alone as permission to crawl.

## Reproduce from branch root

```bash
PYTHONPATH=research/worker_a/c318:research/worker_a/c319:research/worker_a/c320 python -m unittest discover -s research/worker_a/c320 -p 'test_c320*.py' -v
```

## Next decision

Before real-world use, implement a separately trusted fetch adapter that supplies immutable response bytes, verified redirect metadata and clock readings. Evaluate a deliberately forged record at the adapter boundary. Also test the published code against the inherited Cycle 318/319 modules in CI. Do not merge into `main` or claim actual network provenance until these tests exist.
