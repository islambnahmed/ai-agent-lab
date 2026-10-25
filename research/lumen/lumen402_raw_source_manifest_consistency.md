# Lumen 402 — Byte-exact provider manifest consistency gate

**Date (UTC):** 2026-10-25. **Scope:** `islambnahmed/ai-agent-lab`, experimental Gold Lab only.

## Distinct failure hypothesis and evidence

The integrated collector (`scripts/fetch_data.py`) saves the original provider JSON bytes and records both `rawSha256` and `storedSha256` from those exact bytes. However, `parseVerifiedHistorySnapshot` previously checked only that the saved bytes matched `storedSha256`; it did **not** check whether `rawSha256` contradicted that digest. An internally inconsistent manifest could therefore be accepted as a verified raw-source snapshot. This is a provenance-contract issue, not a claim that SHA-256 itself is broken or that a malicious party cannot rewrite an unsigned manifest.

## Reversible correction

- Created `sandbox/lumen-402-raw-provenance-consistency` from the verified integrated head `42d46c0e21525c5e20901cc4368044bb0e3abad7`.
- In `products/gold-forecast/journal.mjs`, require `rawSha256 === storedSha256` before checking the digest of the stored snapshot bytes. This is appropriate for the **new byte-exact collector**; intentionally normalized legacy snapshots require re-fetch and must not be relabeled byte-exact.
- Added a regression in `tests/raw-source-compat.test.mjs` showing that a correct saved snapshot plus contradictory raw digest is rejected.
- Corrected an older `tests/readiness.test.mjs` fixture that intentionally used a fake, unequal raw digest; it was valid under the old normalized-storage contract but not under the new byte-exact contract.

## Independent verification

- Final integration SHA: `6c8ebcb4b6f3c73ede49597f2bcf39c024ccc5d8`.
- [Gold Lab MVP tests, run 40159720884](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40159720884): **completed / success**; unit log confirms **94/94 Node tests** and **13/13 Python tests** passed.
- [AI Agent Lab CI, run 40159720918](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40159720918): **completed / success**.
- [Base-to-head comparison](https://github.com/islambnahmed/ai-agent-lab/compare/42d46c0e21525c5e20901cc4368044bb0e3abad7...6c8ebcb4b6f3c73ede49597f2bcf39c024ccc5d8): 3 commits ahead, 0 behind; exactly 3 Gold Lab files changed.
- The intermediate commits `5d4ae0b` and `de76670` failed Gold CI because of the obsolete fixture. The final SHA passed after fixing that fixture; do not describe the intermediate heads as passing.

## Prospective evidence check and limits

- GitHub Actions artifacts for the original forecast-issuance run `38282833087` were queried: the API returned **zero artifacts** for that run. The previous integrated run `40148275307` also returned zero artifacts. This does not establish that no other authorized storage holds the vintage; it only rules out these two workflow-artifact collections.
- The original 2026-10-12 raw provider response remains unverified/unrecovered. No live XAU price, forecast maturity, prospective MAE, model improvement, or trading edge is asserted.
- Digest consistency detects contradictory manifest metadata, but an attacker who can rewrite both bytes and all unsigned digests remains outside this guarantee. A trusted independently timestamped receipt and retained source vintage are still needed.
- No changes to `main`, peer fields, credentials, security settings, or external accounts. The correction remains experimental.

## Next decision

Stop accumulating generic synthetic tests. Seek a new independently timestamped provider observation with the same close definition and frozen source bytes in authorized storage; then validate first-observed time and source revision policy before computing prospective skill against persistence. If source access remains blocked, work on a different evidence-generating project rather than repeating unavailable-source probes.
