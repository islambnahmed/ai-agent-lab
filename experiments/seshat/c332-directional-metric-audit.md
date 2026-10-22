# Seshat C332 — Directional-metric abstention and possible provider flat-close drift

Date: 2026-10-22. Status: independent audit / no production change.

## Question
Does the existing `directionAccuracy` measure actual directional forecasting ability for the persistence baseline, or is it counting no-change forecasts as directional misses/hits?

## Evidence (main)
- `products/gold-forecast/forecast.mjs`, blob `2cd3731fbb764967387270b0aeafa4ed25fafabd`: directionAccuracy is `100 * mean(sign(point-originClose) === sign(actual-originClose))`.
- `products/gold-forecast/reports/readiness-20261012.json`: 1-close selected model is persistence, with validation n=129 and directionAccuracy=0.7751937984496124%; audit n=65 and directionAccuracy=15.384615384615385%.
- `products/gold-forecast/models.mjs` persistence predicts exactly the origin close (also tested in `tests/forecast.test.mjs`).

## Deduction
For persistence, predicted change is exactly zero, so the reported directional score equals the fraction of actual *exactly unchanged* target closes, not directional skill.
- Earlier validation: 1 unchanged outcome / 129 = 0.7752%.
- Later audit: 10 unchanged outcomes / 65 = 15.3846%.
- Ratio of observed exact-flat shares: 19.85x.

This is a *diagnostic lead*, not proof of stale provider data. Different time windows, calendar composition, quote rounding, weekends, and source cadence could explain the difference. Raw provider vintages are not present in GitHub; do not infer which dates are flat or claim causality.

## Standalone experiment
A pure Node 22 audit implements `directionDiagnostics`: participation/abstention, conditional hit rate among nonzero directional calls, explicit actual-flat counts, and two fixed always-up/down descriptive comparators. Seven deterministic local tests passed:
1. Persistence with changing outcomes: legacy 0%, active 0, conditional hit rate null.
2. Persistence with flat outcomes: legacy 100%, active 0, conditional hit rate null.
3. Always-up on 60/40 outcomes: 60%, equal to fixed always-up comparator.
4. Ten selective correct calls out of 100: 100% conditional accuracy but only 10% participation.
5. Active call when actual is flat is a miss.
6. Explicit symmetrical minimum-move threshold.
7. Invalid inputs rejected.

## Interpretation
Do not rank or promote models using legacy directionAccuracy in isolation. MAE remains the preregistered primary loss; do not retrospectively change model selection. Conditional accuracy can be gamed by abstention and must be reported with participation and fixed comparators. Flat-close incidence is a *data-quality investigation*, not an investment edge.

## Next falsifiable test
With authorized, provenance-preserved raw daily observations and original vintages: count exact zero returns by day of week and by month; distinguish true zero closes from repeated stale vendor quotes; compare audit versus validation without overwriting original receipts. Add a separate non-promotion diagnostic to CI only after source validation. Do not change live predictions or claim skill.

## Boundaries
No main-branch change, no external purchases, no live price collection, no claims of prospective performance. Git branch and local evidence are independent of any existing worker's state.
