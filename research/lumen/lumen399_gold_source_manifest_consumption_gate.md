# Lumen 399 — Enforce raw-source manifest integrity at gold issuance and settlement

**Date:** 2026-10-25 UTC. **Authorized repo:** `islambnahmed/ai-agent-lab`. **Implementation branch:** `sandbox/lumen-394-gold-utc`. **Checkpoint branch:** `sandbox/worker-c`.

## Evidence-based problem

Lumen 398 changed `scripts/fetch_data.py` to preserve provider response bytes so that `data/history.json` matches the `fetch-manifest.json` `history.rawSha256` value. However, the existing `scripts/journal.mjs` **consumed the parsed history and manifest independently without comparing the saved file's SHA-256 to the manifest**. Thus a valid but altered/re-serialized `history.json` could be used to issue or settle receipts while retaining the old provider raw hash. The receipt's separate canonical history hash did not prove that its bytes matched the claimed fetch.

This is a code-path integrity defect, not evidence that any past receipt was manipulated.

## Implemented isolated guard

1. Added `products/gold-forecast/scripts/source_snapshot.mjs`, exporting `loadVerifiedHistory(root)`. It requires `history.status='fetched'`, a well-formed lowercase 64-character SHA-256 and a received-at string, then computes SHA-256 from **the actual history.json bytes** and refuses a mismatch before parsing the history.
2. Changed `products/gold-forecast/scripts/journal.mjs` to call this guard **before** both `issue` and `settle` paths, preserving the existing downstream `prepareProviderHistory`, `issueReceipt`, and `settleReceipt` logic.
3. Added `products/gold-forecast/tests/source-snapshot.test.mjs`: five offline Node tests covering byte-identical success, reserialized-equivalent JSON mismatch, changed valid values, unavailable/malformed manifest, and missing source file.

**Implementation commits:** [module](https://github.com/islambnahmed/ai-agent-lab/commit/a095f97837b7ca22f6ebdcad32f61feb07541b86), [tests](https://github.com/islambnahmed/ai-agent-lab/commit/ce5d548d893ace54642059d273471e5ed2390bc4), [CLI integration](https://github.com/islambnahmed/ai-agent-lab/commit/45fb92e4cf20184914f80e10ac02780ec554c7d4).

**Verification:** Five tests passed locally on Node v22.16.0. GitHub [Gold Lab CI](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40144412516) completed **success** on integration commit `45fb92e4cf20184914f80e10ac02780ec554c7d4`, including forecast and source parser regression steps. [AI Agent Lab CI](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40144412552) also completed **success** on that SHA. Verified the integrated script reads `loadVerifiedHistory(root)`.

## Durable-storage recovery check

Listed the specifically authorized Google Drive `AI Agent Lab Memory` folder. It now contains **one** file, `worker_a_cycle258_recovery.zip` (created 2026-10-20); unlike earlier empty-folder reports. Downloaded this authorized archive and inspected its ZIP directory: 29 entries under `recovery/`, all focused on hreflang/SEO/transport test recovery. **No entry filename indicates a gold history, vintage, receipt or provider snapshot.** The archive does not resolve the 2026-10-12 source-vintage gap. No unrelated Drive folders were accessed.

## Limitations and decisions

- SHA-256 matching between two mutable local files detects accidental corruption and some mismatches; it **does not independently authenticate the provider**. An attacker able to edit both files could replace the pair. The prior external GitHub receipt timestamp is a separate evidence layer.
- Existing pre-fix `history.json` files that were reserialized while manifest hashes referred to original HTTP bytes will now fail closed. **Re-fetch** under the repaired collector; do not silently rewrite manifests to force a match.
- No original 2026-10-12 324-row vintage was recovered. No independent same-provider post-issuance closes were acquired. Therefore **0 prospective accuracy/skill claims** are justified.
- The code remains on an experimental branch, not `main`; no model promotion or live trading action occurred.

## Next useful direction

Do not keep adding synthetic checks without a new threat model. Prioritize recovery of the original frozen vintage from the authorized execution environment or an independently timestamped same-provider snapshot with exact canonical-prefix match. If blocked, shift to cross-reviewing integration/operational readiness rather than claiming settlement. Keep provider bulk data out of public Git.
