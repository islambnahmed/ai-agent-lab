# Khepri Experiment 353 — JSON provenance equality and byte-stable feature selection

Date: 2026-10-21. Research branch only; no production changes.

## Independently reproduced correction to Experiment 352
The previous candidate compared each top-level field with `Object.is`. Independently JSON-decoded records with identical nested metadata therefore triggered a **false conflict**. Reordering keys inside a nested metadata object is semantically irrelevant for JSON but changes object identity.

A first fix using recursively sorted object keys for equality solved that rejection but revealed a second counterexample: it returned the first input row unchanged. Thus `JSON.stringify(availableFeatures([a,b])) !== JSON.stringify(availableFeatures([b,a]))` for equal JSON records with different key insertion orders. Any downstream JSON-based content hash becomes order-sensitive.

## Tested research candidate
- Compare all eligible same-vintage records using a recursive canonical JSON encoding: sort object keys, preserve array order, reject non-JSON and cyclic metadata.
- Fail closed on true same-vintage conflicts, including shadowed older releases.
- Canonicalize **returned** records and sort feature keys, not just compare fingerprints.
- Retain publication-time and staleness guards. Do not invent source priority.

**Offline results:** 31/31 Node tests pass: 3 original repo feature tests, 17 prior experiment regressions, 11 new tests. The new suite includes 720 input permutations, 5,000 seeded JSON key-order permutations and 5,000 deliberate metadata mutations, and a second-domain SEO example.

## Limits
These are deterministic synthetic tests, not evidence that vendor data contains the problem. Canonical output is not raw original bytes; raw vendor records must be retained separately if required. Non-JSON metadata is rejected by policy. Timestamp text aliases remain conflicts by design. Production ingestion should bound JSON size/depth and use immutable parsed snapshots. No full integration suite or real historical vendor dataset has been tested. **Do not merge without review.**

## Reproducibility
Local artifact: `khepri_exp353_reproducible.zip` (source, original and previous candidate, tests, TAP results, SHA256SUMS). Run: `node --test experiment.test.mjs exp352-regression.test.mjs exp352-extra.test.mjs tests/features.test.mjs`.
