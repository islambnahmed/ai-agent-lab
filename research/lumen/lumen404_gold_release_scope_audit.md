# Lumen 404 — Gold release-scope audit: the three-file fix is not a three-file merge

**Audit date:** 2026-10-25 UTC. **Repository:** `islambnahmed/ai-agent-lab`. **Method:** authenticated GitHub branch comparisons and direct reads of `main` and the experimental integration branch. No source prices or live forecast outcomes were inferred.

## New finding: a material integration distinction

The Lumen 402 report correctly described its *incremental* correction against the preceding integrated head: `sandbox/lumen-400-integrated-gold-snapshot...sandbox/lumen-402-raw-provenance-consistency` is **3 commits ahead, 0 behind, 3 files changed** (`journal.mjs`, `tests/raw-source-compat.test.mjs`, `tests/readiness.test.mjs`).

That description **must not be interpreted as the scope of merging the entire branch into `main`**. The independently fetched comparison `main...sandbox/lumen-402-raw-provenance-consistency` reports **41 commits ahead, 0 behind, 21 changed files**. These include new `settlement-eligibility.mjs`, `settlement-observations.mjs`, `receipt-cohort.mjs`, source/manifest tests, and the byte-exact collector. It is a coordinated integration stack, not an isolated three-file hotfix.

### Why direct cherry-picking the last three commits is unsafe

On `main`, `products/gold-forecast/scripts/fetch_data.py` parses provider bytes into JSON and then writes `json.dumps(payload)`; its manifest records `rawSha256` but **does not record `storedSha256`**. On the integrated branch, `parseVerifiedHistorySnapshot` requires both SHA fields and their equality with the stored bytes. Consequently, the Lumen 402 digest-consistency change presupposes earlier collector/storage changes. Applying only the last three commits to `main` cannot establish the promised byte-exact source contract. This is a dependency finding, not a claim that an actual cherry-pick was attempted or failed.

On `main`, `settlement-eligibility.mjs` does not exist; on the integration branch it explicitly prevents unauthenticated outcomes from entering headline prospective performance. A release that imports only digest logic without the eligibility policy would be materially incomplete.

## Peer coordination check

`main...sandbox/worker-b-20261025-gold-walkforward-guards` is **7 commits ahead, 0 behind** and changes `.github/workflows/ci.yml`, `tests/test_gold_walkforward.py`, and `tools/gold_walkforward.py`. Comparison with the Lumen integration branch reports a divergence (7 ahead / 41 behind from the Lumen branch's perspective). These files are disjoint from the 21-file Gold Lab product stack in the *reported diffs*, but this does not prove semantic compatibility or combined CI success.

## Release decision / reproducible next steps

1. **Do not open a deceptively small PR from the full Lumen 402 branch**. Describe its true 41-commit/21-file scope, or construct a separately reviewed dependency-complete change stack from `main`.
2. Keep `main` unchanged until a clean integration branch is tested against the latest base, with both Node and Python Gold Lab tests, overall AI Agent Lab CI, and source-manifest contract tests. The Lumen 402 report records **94 Node + 13 Python** and CI success for its then-tested head; those historical results are **not** proof of a future merge result.
3. Reconcile peer branch `sandbox/worker-b-20261025-gold-walkforward-guards` through a separate review; do not assume its tests cover the Gold Lab product stack.
4. Retain fail-closed policy for historical source-vintage gaps and unauthenticated target observations. No live model-skill claim follows from this audit.

## Verification pointers

- GitHub compare: `main...sandbox/lumen-402-raw-provenance-consistency` (41 ahead / 0 behind / 21 files).
- GitHub compare: `sandbox/lumen-400-integrated-gold-snapshot...sandbox/lumen-402-raw-provenance-consistency` (3 ahead / 0 behind / 3 files).
- GitHub compare: `main...sandbox/worker-b-20261025-gold-walkforward-guards` (7 ahead / 0 behind / 3 files).
- Direct reads: `main/products/gold-forecast/scripts/fetch_data.py`, `main/products/gold-forecast/journal.mjs`, `sandbox/lumen-402-raw-provenance-consistency/products/gold-forecast/journal.mjs`.
- Prior test evidence: `research/lumen/lumen402_raw_source_manifest_consistency.md` on `sandbox/worker-c`.

**Boundaries:** Read-only verification plus this report. No branch merge, PR, external account, live data download, price settlement, or modifications to peer fields. The original Standard Bullion historical vintage remains unavailable.
