# Worker A — Cycle 71: candle availability vs nominal forecast time (2026-10-12)

## Finding
The 713-row XAU/USD historical CSV used in cycles 67–70 was parsed as nominal UTC 5-minute timestamps, but its provider's timestamp convention (candle **open** or **close**) and quote publication delay have **not** been independently established. A candle stamped 12:00 can represent 12:00–12:05; its **closing price is unavailable at 12:00**. Claiming a 12:00 forecast using that close would leak future information. A 12:05 issuance using the same open-stamped candle can have a genuine 75-minute close-to-close target at 13:20. A two-minute late issue at 12:07 has only 73 minutes to that target.

This distinction does **not** by itself invalidate descriptive historical close-to-close MAE from cycles 67–70 if every candle has the same consistent timestamp shift. It **does** prevent claims of real-time issue-time validity or independently witnessed 75-minute prospective skill.

## Tested corrective artifact
- Added `bar-availability-audit.mjs`: explicit `open`/`close` convention, explicit 0–5-minute publication delay, and issue-time checks. There is no silent convention default.
- Added `bar-availability-audit.test.mjs`: 11 adversarial tests, including future close leakage, delayed issuance, publication lag, already-known outcomes, malformed timestamps, and wrong horizon.
- Locally ran 28/28 tests: 11 new + 17 cycle 69–70 tests; no real quote data was downloaded or retested in this cycle.
- Published and read back both code files in authorized `sandbox/worker-a` branch. Verified Git blob SHAs:
  - module `a6ce74c2a22e014d94abb3ed80e4c98e0f667f75`
  - tests `8f2dcb7bee1b75dc8774186bc2ef2dcef7c0ccb4`

## Evidence limits
The synthetic timing examples demonstrate a **causal-availability defect class**, not that the particular public CSV actually uses open-stamped candles. No independent issuance witness, provider timing documentation, data vendor authenticity, live target capture, or predictive advantage has been established. The check assumes constant publication delay for origin and target and cannot authenticate user-supplied times.

## Next
1. Obtain verifiable vendor documentation for whether 5-minute timestamps denote opening or closing times, timezone, and release latency.
2. Reject any prospective forecast whose issue time predates the input candle close availability; report effective horizon from actual issue time.
3. Preregister a future quote before its target and capture outcomes under the prospective protocol. Keep the historical 2-day comparison labeled exploratory.
