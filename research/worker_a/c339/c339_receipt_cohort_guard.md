# C339 — Gold Lab: prevent mixed prospective receipt cohorts (2026-10-24)

## Verified failure mode

On `main`, `products/gold-forecast/scripts/journal.mjs` issues horizons `h1`, `h7`, and `h30` in a loop. For each horizon, an existing receipt filename is silently skipped and a missing one is issued from the **current** provider snapshot and code commit. If the first run is interrupted after writing h1, then a later run with the same latest provider date but revised prices/code can write h7 and h30 from a different history vintage. The three files appear to be one dated cohort but may have incompatible issuance times, snapshots and code versions. This is a deterministic control-flow defect; no production corruption is claimed.

## Change

- Introduce `receipt-cohort.mjs`, a small fail-closed checker for the three ordered horizons. It rejects partial cohorts, mismatched origins/horizons, code commits, issue timestamps, historical hashes/lengths, and source snapshot metadata. The CLI also calls the existing per-receipt `verifyReceipt` integrity check.
- Before writing any receipt, preflight all three expected filenames. A complete consistent cohort is preserved; a partial or inconsistent cohort stops with an actionable error rather than silently filling gaps.
- Prepare **all three** new receipts and check consistency before writing any of them. The existing `wx` create-only writes and immutable vintage behavior remain.
- Add the new module and issuer script to the pre-issue dirty-file check.
- Leave settlement behavior unchanged in this standalone patch; reconcile with open PRs #10 and #12 during integration.

## Verification

- Local `node --test tests/receipt-cohort.test.mjs`: **9/9 passed** (empty, complete, partial, horizon mismatch, history hash mismatch, issue/code mismatch, snapshot mismatch, malformed slots, verifier callback).
- Local `node --check` passed for helper, test and modified CLI source.
- GitHub Actions **push** run 40062182006 and **pull_request** run 40062182065 both completed successfully for commit 58c8455ec2433b1bac93b7ef365449c71d633f92. The workflow executes Node syntax checks, the full Gold Lab Node test glob (including the 9 new tests), Python syntax checks, and Python source tests. Evidence: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40062182006 and https://github.com/islambnahmed/ai-agent-lab/actions/runs/40062182065 .
- No provider fetch, live issuance, production data change, or verified prospective forecast skill is claimed.

## Limitations and recovery

The three file writes are **not a filesystem transaction**. A crash can still leave a partial set; the guard deliberately refuses to auto-repair it with a different vintage. An operator must inspect the original receipt(s), saved vintage, and publication anchors before deciding how to recover. Never delete a published receipt to rewrite historical evidence. Existing complete cohorts are preserved unchanged. This check does not prove price authenticity, close-time availability, or prospective forecast skill.

## Integration note

PR #10 modifies the issuer's snapshot verification and dirty guard; PR #12 modifies its settlement gate. This change also touches the issuer, so all three patches need a deliberate conflict resolution. The cohort guard is complementary to both and must not undo their fail-closed behavior.
