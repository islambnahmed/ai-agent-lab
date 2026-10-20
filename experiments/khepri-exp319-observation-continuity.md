# Khepri Experiment 319 — Post-Issue Observation Completeness
Date: 2026-10-20. Authorized scope: `islambnahmed/ai-agent-lab`.

## Hypothesis and counterexample
For `calendar: "observations"`, `products/gold-forecast/journal.mjs` settles with `index = historyLength + horizon - 1` when `targetDate` is null. Its history hash authenticates the **pre-issue prefix**, not completeness of later observations. A refreshed provider snapshot that silently omits a close after issuance can shift the target without failing the prefix check.

A controlled fixture with 165 historical observations and 32 future observations reproduced this at h=1, 7, and 30. The original settlement logic returned `matured` on the *next* close after a pre-target omission, rather than quarantining it. In 1,000 deterministic h=7 omission trials, 217 omissions were within the first seven future closes and all 217 shifted the target; 783 post-target omissions did not. This is a synthetic counterexample, not proof of a real provider omission.

## Actual repository exposure
All three prospective receipts in `products/gold-forecast/reports/prospective/2026-10-11-h{1,7,30}.json` have `calendar: "observations"`, `targetDate: null`, and `historyLength: 324`. Therefore the failure mode is relevant to the actual receipts, but **none has been proven incorrectly settled**. Inspected `journal.mjs`, `data.mjs`, `historical-integrity.mjs`, and receipt metadata on main.

## Prototype
A fail-closed `guardedSettle` prototype requires a separately authenticated complete sequence of future close dates before promoting an observation-indexed outcome to `matured`. It checks the expected first h dates against the refreshed series and delegates to the original settlement function only after continuity passes. No witness => `unverifiable`; missing close => `quarantined`. A forged witness with a compromised verifier still fools the guard, so **real independent witness verification is an unsolved integration dependency**. The existing three real receipts would remain unverifiable without such evidence, not automatically wrong.

## Tests and caveats
20/20 Node tests passed: h=1/7/30, pre/post-target omissions, 1,000 deterministic trials, absent and forged witnesses, and transfer to dated website-traffic events. The test uses unchanged settlement logic from an earlier lab snapshot plus the historical validator and a narrowed `prepareHistory` adapter; current main's settlement index and prefix checks were independently inspected and match. This is **not** full production integration and uses synthetic prices. The complete reproducible bundle is available in the conversation artifact `khepri_exp319_reproducible.zip`.

## Recommendation
Do not treat index-only `observations` settlement as independently verified prospective evidence without a completeness witness or verified calendar. Preserve raw provider response manifests, represent uncertain outcomes as `pending/unverifiable`, and run an end-to-end integration test before changing production. No production files, workflows, or peer artifacts were modified.

## Reproduce
`node --test tests/*.test.mjs` (Node 22+), from the extracted experiment artifact root.