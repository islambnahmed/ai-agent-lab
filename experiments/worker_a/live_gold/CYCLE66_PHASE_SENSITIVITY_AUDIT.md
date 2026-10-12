# Worker A — Cycle 66: UTC-anchored phase sensitivity (2026-10-12)

## Finding
The previous disjoint 75-minute replay sampled origins at `segment_start + 15` five-minute bars, then every 15 bars. That makes the selected evaluation phase depend on the **first row of the downloaded file** and on where contiguous segments begin. Changing the slice boundary can change which forecasts are evaluated even when the underlying prices are unchanged. Non-overlap alone is not sufficient protection against arbitrary phase selection.

## Corrective experiment
Implemented locally `phase-audit-75m.mjs` and `phase-audit-75m.test.mjs` to assign every eligible 75-minute forward candle-close comparison to one of 15 UTC-epoch-anchored origin phases. Within each phase the forward windows are non-overlapping; across phases they overlap and **must not be treated as 15 independent trials**. Report all phase counts and model errors, not only the phase favorable to a model.

An adversarial seeded 500-bar synthetic random walk produced **14 phases favoring persistence, 1 favoring drift**. This proves phase-dependent winner reversal is possible in constructed data; it does NOT establish the effect on real gold prices.

## Reproducibility and limits
- Local: `node --test five-minute-75m.test.mjs disjoint-75m.test.mjs phase-audit-75m.test.mjs` => **28/28 passed** (20 previous + 8 new).
- On the locally archived **31-row** public 5-minute historical preview, there is only **1** eligible forecast (phase 10). Persistence AE ~$3.07; linear drift AE ~$11.30. Not enough to infer skill.
- Attempt to download full 35,954-row public historical file into execution container failed; no full-sample performance claim.
- Dataset provider truth, executable prices, independent capture timestamps, and prospective precommit are unverified.
- Local source SHA-256: `6837642ed61875f92dce317093decb0a012cb5fd18a6bcc8ae5a894191fc0d8a`; tests SHA-256: `fe8b684a76131d05014d13798317821704a9b5d3c6e79148f50f2f4900abb3ee`.

## Next
Publish the tested phase-audit source when a normal authorized write succeeds. Obtain complete reproducibly hashed market data, run all 15 predeclared phases, and evaluate prospective fixed-horizon forecasts. Do not cherry-pick phase or report correlated counts as independent observations.
