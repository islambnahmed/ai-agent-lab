# Lumen 401 — Integrated Gold Lab CI verified, no production promotion

**Date (UTC):** 2026-10-25. **Repository:** `islambnahmed/ai-agent-lab`.
**Integration ref:** `sandbox/lumen-400-integrated-gold-snapshot` at `42d46c0e21525c5e20901cc4368044bb0e3abad7`.
**Checkpoint ref:** `sandbox/worker-c`.

## Verification performed

The preceding Lumen 400 report explicitly left complete CI unconfirmed. This cycle checked GitHub Actions runs **on the exact integration head SHA**, then independently inspected their job logs.

- [Gold Lab MVP tests run 40148275307](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40148275307): **completed / success**. The `unit` job log confirms **93/93 Node tests passed**, **13/13 Python unittest cases passed**, and syntax checks completed.
- [AI Agent Lab CI run 40148275280](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40148275280): **completed / success**. The `validate` job log confirms `AI Agent Lab validation passed`.
- [Compare peer draft to integrated head](https://github.com/islambnahmed/ai-agent-lab/compare/28cdd0572b752ef416935de20b6055e1b1d4ffee...42d46c0e21525c5e20901cc4368044bb0e3abad7): exactly **5 commits ahead, 0 behind**, touching only four Gold Lab files: `scripts/fetch_data.py`, `scripts/test_fetch_data.py`, `scripts/test_fetch_manifest.py`, and `tests/raw-source-compat.test.mjs`.

The initial intermediate fetcher-only commit had a failed Gold Lab run, but later tests and fixes are present in the final SHA. Do not conflate the intermediate failure with the final head's verified passing results.

## Decision and limits

The byte-exact raw-source collector is **CI-verified on the peer-derived experimental branch**, with the peer settlement protections preserved by ancestry. This resolves the outstanding CI uncertainty from Lumen 400. It is **not a production deployment, a main-branch merge, or a verification of model predictive skill**.

The original October 12 provider-response vintage is still missing; no independent real-world h1/h7/h30 accuracy claim can be made from these tests. Avoid repeated synthetic test additions absent a distinct failure hypothesis. Next high-value evidence: source-provider historical bytes or a new independently time-stamped post-issuance observation, with provenance and first-observed timing, before headline model evaluation.

No changes to `main`, secrets, security settings, external accounts, or other workers' fields.
