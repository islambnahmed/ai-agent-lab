# Keystone SEO snapshot benchmark — 2026-10-22

## Provenance
- Source: `experiments/seo-snapshot-audit/audit.py` on `sandbox/worker-b-seo-audit-20261022`
- Verified exact Git blob SHA: `fc873d5024aad0dec8d12609e33fc7f0845f052d`
- Source was reconstructed from the connector read and verified with `git hash-object` before local execution.
- Prior adversarial regression suite: **17/17 passed on this exact branch version**.
- Independent synthetic benchmark: **30/34 cases passed**; finding-level TP=26, FP=2, FN=2 (precision=92.86%, recall=92.86%); internal-link counts correct in 34/34.
- Synthetic, hand-labeled HTML only. No live site, Google indexing, search ranking, or production precision claims.

## Four accessible-name counterexamples
1. `<a href="/a"><span aria-hidden="true">Invisible</span></a>` — missing accessible name is **not flagged** (FN).
2. `<a href="/a" aria-labelledby="label"></a><span id="label">Go to page</span>` — accessible name is **falsely flagged missing** (FP).
3. `<a href="/a" title="Open details"></a>` — title fallback accessible name is **falsely flagged missing** (FP).
4. `<a href="/a"><svg aria-hidden="true"><title>Invisible</title></svg></a>` — missing accessible name is **not flagged** (FN).

The benchmark intentionally measures the link-name heuristic against a limited manually labeled subset of accessible-name semantics. A complete accessible-name implementation is out of scope for an HTML snapshot parser. Do not call the 92.86% score a representative real-world accuracy estimate.

## Decision
The previous 17 regression tests now directly validate the exact GitHub branch file (not merely a fuller local reference). The remaining failure class is accessibility-name interpretation, not the URL/internal-link/script regressions from the previous cycle. Next: add a small, independently labeled fixture suite to CI and either implement bounded aria-hidden / aria-labelledby / title support or explicitly downgrade link-name findings to unverified heuristics.

## Recovery
Local reproducible files in Keystone cycle 127 archive: `audit.py` (verified blob), `test_regressions.py`, `benchmark.py`, `benchmark_result.json`. Run `python -m unittest -v test_regressions.py` and `python benchmark.py`. This branch report is not proof that CI runs these tests.
