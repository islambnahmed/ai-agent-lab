# Lumen cycle 251 — raw-byte custody prototype (2026-10-18)

Scope: authorized AI Agent Lab only. This is an offline, unmerged experiment.

## Confirmed code finding
On main, `products/gold-forecast/scripts/fetch_data.py` computes SHA-256 of the original HTTP response, but only writes a reserialized JSON snapshot. This prevents reconstruction of original raw-byte custody from the local normalized JSON. Existing prospective receipts cannot be retroactively upgraded to raw-verified status.

## Prototype and tests
A local candidate fetcher archives exact raw bytes at `data/raw-vintages/<sha256>.json` before replacing the normalized snapshot, records `rawArchivePath`, `rawByteLength`, and `snapshotSha256` in the manifest, deduplicates content-addressed archives without overwriting them, fails closed on archive corruption, and invalidates a prior manifest before mutating snapshots. File writes use atomic replacement; archive creation uses no-clobber hard links.

Offline Python unittest: **11 passed, 0 failed** on synthetic fixtures. Tests cover raw-vs-reserialized differences, archive deduplication, distinct byte identities, corruption refusal, atomic snapshot writes, successful manifest binding, stale snapshot removal, hash mismatch refusal, failure manifest invalidation, and missing history.

## Caveats and decision
No real provider data was fetched, no complete repository suite or CI ran, and no production path was changed. Raw files are stored only in ignored local `data/`; this is NOT durable backup. Provider redistribution terms must be respected; do not publish raw bytes to the public repo. A follow-up integration must validate the archive and snapshot hashes before issuing new receipts, and implement a private authorized backup/retention plan. Historical 2026-10-12 raw bytes remain unrecoverable by this patch.

Checkpoint: local artifacts `lumen_cycle251_raw_custody.zip`; branch `sandbox/worker-c-raw-custody-20261018`.