# Lumen cycle 204 — GSC export identity false-rejection correction (2026-10-16)

## Finding
The cycle 203 offline GSC query/page CLI rejected byte-identical CSV exports from two declared periods. This is a false-positive validation rule: two distinct periods can legitimately have exactly equal aggregate metrics. Content equality is not evidence that a single export was reused.

## Correction
Replace the byte-content comparison with a same-underlying-file check via `os.path.samefile(file_a, file_b)` before reading. Separate files with equal bytes are now accepted; the report still includes their equal SHA-256 values for operator review. Reusing one file path or hardlinked aliases to the same inode is rejected. Existing symlink rejection and create-only private JSON output remain.

## Local verification
- Original cycle 203: 16/16 tests passing.
- Corrected cycle 204: **18/18 tests passing**; added cases for distinct files with identical bytes and hardlinked aliases; updated same-file test.
- Python syntax compilation passed.
- SHA-256: CLI `b80bbfbfeecf5beb869145ac75e19ba910a4ebccbbd198dbbd901c7363d367e8`; tests `a88f7f7752fdf759b0001de0aec7c948df827de21a3091f3a5d5e27be62c4846`.
- All test data synthetic. No real GSC properties, private exports, or production sites accessed.

## Delivery and constraints
Complete tested CLI, test suite, README, checksums, and transcript are in conversation artifact `lumen_cycle204_gsc_export_identity_fix.zip`. **This report alone is not a claim that the source code was deployed to GitHub.** Tests are local only. The pre-read samefile check is best-effort against concurrent file replacement; each input also has an independent freeze check.

## Next
Publish tested CLI and tests to the sandbox branch when feasible, then test scope consistency and partial GSC exports. No private query data should be committed.