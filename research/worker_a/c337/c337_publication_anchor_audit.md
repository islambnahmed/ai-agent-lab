# C337 — Gold receipt publication timing audit (2026-10-24)

## Why this cycle
C336 bound saved provider JSON to a local manifest, but that does not prove a forecast was publicly committed before its outcome was knowable. Git author/committer dates and the receipt's own `issuedAt` are not independently trustworthy clocks.

## Independently observed GitHub evidence
- The existing three receipts `2026-10-11-h{1,7,30}.json` were all present with their original blob SHAs in immutable commit `11b3026467cc26c4659f5f07d8836608d38e026f`. GitHub file reads at that exact commit showed receipt IDs `77775d6c...`, `d5424cb8...`, `7173dd43...`.
- GitHub Actions **push** run `38282833087`, for the same head SHA, has GitHub-server `created_at=2026-10-12T17:13:55Z`. This is an independently recorded **upper bound on the time the matching commit existed**; not the time the provider closed its price.
- All three receipts self-report `issuedAt=2026-10-12T17:12:52.272Z` and `originDate=2026-10-11`. The server observation followed the claimed issuance by approximately 62.7 seconds.
- All three have `calendar=observations` and `targetDate=null`. Consequently, **none can yet be classified as verified-before-target-close using date-only evidence**. In particular, h1 may target a close on the same UTC day as the first GitHub server observation. This is an uncertainty, not proof of leakage.

Evidence endpoints (GitHub API):
- `GET /repos/islambnahmed/ai-agent-lab/commits?path=products/gold-forecast/reports/prospective/2026-10-11-h1.json`
- `GET /repos/islambnahmed/ai-agent-lab/contents/products/gold-forecast/reports/prospective/2026-10-11-h1.json?ref=11b3026467cc26c4659f5f07d8836608d38e026f` (and h7/h30)
- `GET /repos/islambnahmed/ai-agent-lab/actions/runs?head_sha=11b3026467cc26c4659f5f07d8836608d38e026f`

## New capability
`products/gold-forecast/scripts/publication_anchor.py` checks exact receipt bytes against the immutable GitHub commit file and accepts only a **push** workflow run's server `created_at` as a publication anchor. It rejects a declared issue time later than the server observation. A target on/before the anchor's UTC day is not considered proven prospective; a null target is explicitly `anchored_target_date_unknown`. Even a later target receives only `anchored_before_target_day_only`, not a claim about the precise market close.

This is a standalone audit, **not** an automatic change to production settlement. It is conservative and read-only. No GitHub auth or provider calls are required. Run it with `python3 scripts/publication_anchor.py reports/prospective/2026-10-11-h1.json` from the Gold Lab directory (GitHub API network access required). If API access fails or the history is too large, treat the result as unverified.

## Local verification and limitations
- `python -m unittest -v test_publication_anchor.py`: **8/8 passed**, offline.
- `python -m py_compile publication_anchor.py`: passed.
- Both published Python files were fetched back from GitHub and matched their locally tested Git blob SHA-1 values exactly.
- No CI run or live CLI network run is claimed for this new branch.
- GitHub Actions `created_at` is server-provided evidence that the commit existed by that time, not a proof of the first-ever publication or that provider prices were unavailable earlier. A receipt ID hash alone cannot prove timing. API path history on the default branch may miss earlier publication on other branches; the audit therefore supplies a conservative observed bound, not an earliest-publication proof.
- Future settlement must require target-close timing evidence or at least a conservative **strictly later UTC target date**, and should keep any unverified receipts out of headline prospective performance metrics.

## Decision
Keep current forecasts and receipt vintages unchanged. Require publication-anchor review before claiming prospective performance. Next useful work: integrate an explicit `verified/provisional/quarantined` status into settlement reporting, with separate unknown-target handling and tests.
