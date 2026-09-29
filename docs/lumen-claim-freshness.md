# Claim Freshness and Provenance — Lumen experiment

## Problem
Coordination artifacts mix current state with historical checkpoints. A checkpoint can be accurate when written and misleading later if a reader treats it as live state.

## Current executable model
Machine-actionable claims use:
- `observed_at`: strict UTC second-resolution timestamp; future observations are rejected.
- `source_path`: artifact that supported the claim.
- `claim_kind`: `current_state` or `historical_observation`.
- Whole-file provenance: `source_blob_sha`.
- Optional scoped provenance: `source_scope` plus `source_scope_sha`, produced with `canonical_scope_sha`.

For `current_state`, the consumer supplies the current path and provenance. A mismatch returns `refresh`; malformed, partial, or path-inconsistent provenance returns `warning`.

For `historical_observation`, provenance must also be present in `verified_historical_shas`. Merely looking like a 40-character SHA is not enough. The caller is responsible for independently verifying that SHA before supplying it—for example by fetching the historical Git blob, or by recomputing the canonical scoped digest from the historical source data.

## Important trust boundary
`verified_historical_shas` is an input trust boundary, not a verifier. The helper does not itself contact GitHub or reconstruct old source data. A caller that inserts an unverified value into that set defeats the historical-verification guarantee.

Likewise, a verified SHA proves the supplied digest was independently checked; it does not by itself prove arbitrary free-text semantics. Consumers should bind verification to the intended source path/scope in their own retrieval step.

## Why this stays small
The lab already has race-tolerant cycle reconciliation. This experiment avoids another synchronized shared file or atomic multi-file protocol. Freshness is checked at read time against immutable provenance, with scoped digests available so unrelated edits elsewhere in a shared file do not invalidate a claim.

## Evaluation cases
The executable self-test covers:
1. stale whole-file `current_state` -> `refresh`;
2. matching provenance -> `usable`;
3. path/scope mismatch or malformed provenance -> `warning`;
4. future or malformed `observed_at` -> `warning`;
5. historical provenance absent from the independently verified set -> `warning`;
6. verified historical provenance -> `historical`;
7. deterministic scoped digests and rejection of non-portable JSON values.

This is a reversible design experiment, not a mandatory lab protocol.
