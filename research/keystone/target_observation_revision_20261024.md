# Keystone — post-origin target revision audit (2026-10-24)

## Counterexample

The issuance vintage is frozen through \`originDate\`, but \`appendVerifiedVintage\`
only checks revised/missing/inserted closes on or before that date. A provider can
later revise the *target* observation without touching the frozen prefix.
\`settleReceipt\` then recomputes \`actual\`, model error, baseline error, and
coverage from the revised target. Repeated \`npm run settle\` can silently
rewrite descriptive outcomes for the same receipt ID.

This is not evidence that the provider actually revised a target. It is a
reproducible integrity gap in the local settlement workflow.

## Reversible guard

\`settlement-observations.mjs\` records the first locally observed matured
\`{receiptId,horizon,targetDate,actual}\` under ignored
\`data/settlement-observations/<receipt-id>.json\` with exclusive creation.
Subsequent settlements for the same receipt are quarantined if the target date
or actual price changes, or if a previously matured target disappears. Corrupt
local baselines fail closed. Quarantine omits error metrics.

The guard is applied after \`settleReceipt\` and before reporting. Issuance's
dirty-code check now includes this module. No historical data, receipts,
provider requests, external accounts, production branch, or schedules change.

## Tests and scope

- Seven offline unit tests passed locally before upload, including repeated
  settlement, revised target date/price, disappearing target, corrupted
  baseline, and invalid receipt ID.
- An additional end-to-end Node test reproduces the gap using
  \`issueReceipt\` + \`appendVerifiedVintage\` + \`settleReceipt\`, then verifies
  that the first-observation guard quarantines the revised target.
- CI status must be checked on the final branch head; local success alone is
  not a claim of GitHub Actions success.

## Explicit limitations

1. The baseline is **local and mutable**, not an immutable public timestamp,
   an authenticated source vintage, or a proof of predictive skill.
2. The first settlement run may already observe a revised target; no earlier
   source vintage is available to detect that.
3. A deleted private baseline removes continuity; back it up through an
   authorized lab memory path before relying on it for long-term audits.
4. PR #12 independently gates arithmetic \`matured\` outcomes to
   \`provisional\` until publication-before-close evidence exists. On
   integration, preserve the raw arithmetic outcome **before** applying the
   timing gate. Neither guard substitutes for the other.
5. PR #10 and #9 overlap in snapshot-integrity code. Do not blindly merge
   both versions of \`scripts/journal.mjs\`; reconcile source-URL verification,
   vintage overlap checks, first-target observations, and timing eligibility
   in a single reviewed implementation.

## Merge posture

Draft stacked change based on PR #9 branch. Do not merge to \`main\` or
advertise prospective MAE until independent publication and close-time
attestation are available.
