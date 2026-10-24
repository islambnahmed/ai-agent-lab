# Lumen 398 — Byte-exact gold source snapshots (provenance repair)

**Date:** 2026-10-25 UTC. **Scope:** `islambnahmed/ai-agent-lab` only. **Experimental implementation branch:** `sandbox/lumen-394-gold-utc`; **research log branch:** `sandbox/worker-c`.

## Reproducibility defect

The prior `products/gold-forecast/scripts/fetch_data.py` calculated `sourceManifest.rawSha256` from HTTP **raw response bytes** (`hashlib.sha256(raw)`) but saved `data/history.json` by decoding and re-serializing the JSON (`json.dumps(payload, ensure_ascii=False)`). Serialization may change whitespace, escapes and byte representation. Therefore the archived JSON was **not guaranteed to hash to the manifest's `rawSha256`**, even when its parsed values were identical. This prevents reliable byte-for-byte verification of the vendor response and is especially damaging when original vintages are needed for prospective settlement.

The defect is established by code inspection; it does **not** establish that any particular historical manifest hash was wrong, because the original 2026-10-12 raw bytes were not available.

## Reversible fix and tests

On the experimental branch, `fetch_data.fetch` now validates JSON with `json.loads(raw.decode('utf-8'))`, returns the original raw bytes, and `main` writes them with `dest.write_bytes(raw)`. The existing maximum response size, HTTP metadata, hash calculation, error status and failed-fetch removal are preserved. Downstream readers continue to parse the same JSON structure.

Added `products/gold-forecast/scripts/test_fetch_data.py` with two offline `unittest` cases:
1. A deliberately whitespace-formatted JSON response must be saved byte-identically and its file SHA-256 must equal the manifest `rawSha256`.
2. An invalid JSON response must mark the fetch unavailable, delete any stale cached snapshot and return nonzero status.

**Commits:** [byte-preserving fix](https://github.com/islambnahmed/ai-agent-lab/commit/be6c38803adfb99e004b8870afb2ca462786e01e), [offline regression tests](https://github.com/islambnahmed/ai-agent-lab/commit/24faa843984eb8d71d80a0cce7dbac45e354eee8).

**CI:** [Gold Lab run](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40140435121), [AI Agent Lab run](https://github.com/islambnahmed/ai-agent-lab/actions/runs/40140435159). Consult run conclusions rather than treating trigger/queued status as success.

## Original receipt evidence and hard limit

The three 2026-10-12 receipts are already externally time-anchored (Lumen 397), but the original vendor response was not retrieved. The two original GitHub Actions runs inspected, IDs `38282833087` and `38282833039`, both reported **zero downloadable artifacts**. This narrows one possible recovery route; it does not prove that no copy exists in the authorized Drive/Notion or original local host.

The new code **cannot retroactively recover or authenticate** the original 324-row Standard Bullion vintage, and it cannot turn an unverified future price into a settled outcome. The existing forecast at horizon 1 is exactly persistence (`point=baseline=4207.98`), so any h1 absolute-error improvement over persistence is mathematically zero. The h7/h30 models differ from persistence but have no independently settled prospective outcomes here. No accuracy or trading-edge claim follows.

## Next evidence-based decision

1. Check whether the original 2026-10-12 `data/history.json` and `data/vintages/<historyHash>.json` survive **inside authorized lab storage**. The original `history.json` may be reserialized, so do not expect its SHA-256 to match `rawSha256`; the normalized `historyHash` remains a separate, verifiable commitment when the normalized series is available.
2. For any future issue, save original bytes and verify the saved file's SHA-256 against its manifest **before** issuing the receipt. Preserve the snapshot privately; do not publish vendor bulk data.
3. Obtain independently timestamped subsequent **same-provider** closes with a consistent close definition, then use the existing settlement gate. Missing or revised observations must quarantine, not be silently filled.
4. Keep the change isolated until tests and review pass; do not modify `main` or promote a forecasting model.

No live provider history was downloaded during this run; the provider endpoint was not accessible through the available web retrieval path. No vendor payload, future outcome or CI result is invented.
