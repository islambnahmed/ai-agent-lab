# Lumen cycle 129 — Git blob binding for prospective receipt anchors

Date: 2026-10-13. Scope: `islambnahmed/ai-agent-lab` only.

## Verified failure in cycle-128 verifier

`anchor_audit.mjs` checked a receipt's self-recomputed SHA-256 `id`, that the path was `added` in commit `11b3026467cc26c4659f5f07d8836608d38e026f`, and an independent GitHub Actions timestamp. **It did not bind the supplied receipt JSON bytes to the Git blob added in that commit.**

Adversarial counterexample: change the published h1 point from `4207.98` to `999999`, recompute the receipt's `id`, and reuse the genuine commit and Actions run metadata. The old verifier reports `valid: true` with zero problems. This is an offline evidence-substitution vulnerability, **not evidence that the actual GitHub receipt was altered**.

## Local repair and evidence

The revised verifier requires (1) exact raw UTF-8 receipt bytes; (2) a Git blob SHA for each added file from the pinned commit's `files[].sha`; (3) `SHA1("blob "+byteLength+"\\0"+rawBytes)` equals that commit-file SHA; and (4) the parsed raw JSON equals the receipt used in the audit. Missing/mismatched bytes fail closed as `receipt_not_bound_to_commit_blob`.

Fetched GitHub commit `11b3026` and its three published receipt files at that exact SHA. File blob SHAs:
- h1: `78d31625703e4563f38c460420c26134d885dff3`
- h7: `5dbce37a27fe53d950dc4984e3522e9db3620f86`
- h30: `61ce82063472b0385e1a81c4e9137c503db6d61f`

Reconstructed the exact raw bytes and independently reproduced all three Git blob SHAs locally. The repaired verifier accepts the three genuine snapshots and rejects the substituted point. All **12/12** Node tests passed locally (the original 9 plus 3 adversarial tests).

## Limitations

Git blob SHA binding verifies that offline evidence matches the referenced Git commit, assuming the GitHub API commit/file evidence is independently re-fetched. It does not authenticate the gold price provider, prove market close dates, or establish forecasting skill. The verifier is not yet merged or running in CI.

## Recovery

Local artifact: `lumen_cycle129_gold_blob_binding.zip` attached in this ChatGPT run. Contains patched `anchor_audit.mjs`, tests, pinned GitHub evidence, original counterexample, and repaired output. Do not treat this report as a substitute for the executable patch.

Next: publish patched code/tests on an authorized lab branch when GitHub write policy permits; rerun CI; do not merge without code review.
