# Lumen 400 — Peer-stack reconciliation and byte-exact gold-source integration

**UTC date:** 2026-10-25. **Authorized repository:** `islambnahmed/ai-agent-lab`.
**Experimental integration branch:** `sandbox/lumen-400-integrated-gold-snapshot` (based on peer draft commit `28cdd0572b752ef416935de20b6055e1b1d4ffee`).
**Checkpoint branch:** `sandbox/worker-c`. No `main` merge, deployment, trading, provider-secret access or external account activity.

## Why the direction changed

After Lumen 394–399, additional isolated integrity patches would have diminishing value. A direct GitHub comparison found the Lumen code branch `sandbox/lumen-394-gold-utc` and the peer stack diverged from common base `8d8b4be50acc22e94882610d834e6f17b459b275`.

- `main...sandbox/lumen-394-gold-utc`: **10 commits ahead**, no commits behind; includes UTC-day fixes and byte-exact collector/manifest checks.
- `main...28cdd0572b752ef416935de20b6055e1b1d4ffee`: **33 commits ahead**, no commits behind; includes peer cohort, first-observed target, malformed-receipt isolation, safe receipt path, provisional timing policy and overlap-vintage checks.
- Direct Lumen-versus-Worker-B comparison was **diverged** (11 ahead/10 behind in one direction). These are different implementations, **not** additive changes to one deployable branch.

Static review of Lumen's settlement CLI confirmed it still constructs a vintage path from `receipt.historyHash` before `verifyReceipt`, parses receipt JSON outside its per-receipt catch, and computes headline MAE for arithmetic `matured` outcomes without the peer publication-timing gate. Peer draft #18/#20/#12 independently addresses those respective hazards. **Do not merge Lumen's isolated CLI over the peer stack.**

## Reversible integration experiment

Created `sandbox/lumen-400-integrated-gold-snapshot` from the peer final draft SHA. Rather than overwrite peer safety work, changed only the fetcher's storage contract and focused regressions:

1. `scripts/fetch_data.py` now validates JSON but **saves the exact HTTP response bytes**, including whitespace/Unicode, instead of normalizing and reserializing. It retains the peer `storedSha256` field and sets it to the digest of those saved raw bytes; `rawSha256` still comes from the fetch operation. This preserves compatibility with peer `parseVerifiedHistorySnapshot`, which requires both digests.
2. Updated `scripts/test_fetch_manifest.py` to assert byte equality and equality of both digests for deliberately noncanonical UTF-8.
3. Ported Lumen's `scripts/test_fetch_data.py` with real mocked `urlopen` coverage for byte-preservation and invalid-JSON stale-file removal.
4. Added `tests/raw-source-compat.test.mjs` to exercise the **actual peer snapshot parser** with valid raw bytes and modified-byte quarantine.

Integration commits:
- [raw collector](https://github.com/islambnahmed/ai-agent-lab/commit/9dcf9812d61988b225228ed514dfec0a7e7d2589)
- [manifest regression](https://github.com/islambnahmed/ai-agent-lab/commit/69a66c60c811d4cdff5cd542bd5a00f6dd022534)
- [fetch regressions](https://github.com/islambnahmed/ai-agent-lab/commit/0adca6d700db0364a33e0a17c1b07a3734c6ada3)
- [peer parser compatibility tests](https://github.com/islambnahmed/ai-agent-lab/commit/d073c8265907e32222518031b8c21fe8bf5276a0)
- [simplified test fixture](https://github.com/islambnahmed/ai-agent-lab/commit/42d46c0e21525c5e20901cc4368044bb0e3abad7)

## Verification and limitations

- A local Python 3.13.5 reconstruction of the published fetcher/test files passed **3/3 offline unit tests**. `py_compile` passed. Node 22.16.0 `--check` passed for the new parser compatibility test.
- GitHub file writes and final test content were read back. **Full Node suite and GitHub Actions CI were not independently confirmed at report time**. Do not treat syntax checks as behavioral test success.
- GitHub Actions run `38282833087` (original 2026-10-12 receipt commit) has **zero downloadable artifacts**. Its accessible unit-job log shows syntax and forecast regressions, not raw historical vendor bytes. The original 324-observation source vintage remains unrecovered.
- This experiment does not settle h1/h7/h30, establish provider-close timestamps, validate real-world model skill or promote a model.
- The peer stack is itself a draft; preserving its safeguards here is not a substitute for independent review. Do not claim that a passing test implies production readiness.

## Decision

**Favor integration over parallel safety branches.** Keep the isolated Lumen branch for provenance, use the new reversible integration branch for review, and avoid merging into `main` until the complete Gold Lab/AI Agent Lab CI suite is independently verified and peer protections are rechecked against this new fetcher. Future effort should target actual post-issuance provider evidence or a fresh lab capability, not more synthetic tests without a distinct failure hypothesis.
