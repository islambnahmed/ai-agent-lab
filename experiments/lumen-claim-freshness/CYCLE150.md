# Lumen cycle 150 — stale-claim editorial gate (2026-10-14)

## Confirmed counterexamples
The prior offline `validate_claims.py` checked that `checked_on` was not in the future, but did not require a new source review before publication. Two concrete replay cases passed the old validator incorrectly:

1. A Google Cloud eligibility-gated card with `checked_on=2026-09-30` (14 days old on 2026-10-14): old `validate()` returned `[]`; revised gate requests re-verification.
2. A closed Claude cohort card changed to unrecognized `offer_state=closed` and `publication_rule=publish_with_caveat`: old validator returned `[]`; revised gate rejects unknown states.

These are metadata-guard bypasses, not proof the provider claims are false.

## Local evidence
- Original 8/8 regression tests passed, but did not cover these cases.
- New 10/10 targeted tests passed against a revised local standard-library-only validator.
- Tested 2026-10-14 ledger: all seven cards pass on their original checked date.
- No live provider-page re-verification and no publication of a social post.
- No production system changed.

## New conservative editorial policy (heuristic, not provider SLA)
- Closed cohort: review source within 1 day.
- Eligibility-gated credits and limited programs: review within 7 days.
- Process guidance and documentation updates: review within 30 days.
- Unknown state: fail closed; never infer eligibility or live offer status from a passing metadata check.
- `--as-of YYYY-MM-DD` allows reproducible historical checks.

## Follow-up
Deploy only after independent review of the chosen age thresholds and publishing workflow. A passing gate verifies metadata consistency and freshness **only**, not actual source truth. Current local code/tests are bundled with this cycle's artifact.