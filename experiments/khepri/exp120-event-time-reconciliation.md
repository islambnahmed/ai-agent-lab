# Khepri Experiment 120 — Event-time-aware feed reconciliation
Date: 2026-10-10. Scope: authorized AI Agent Lab. Source: products/gold-forecast/app.mjs on feature/gold-forecast-mvp-20261008 (read-only).

## Finding
The prior cross-source denomination alert can conflate different observation times with a unit mismatch. A price jump between quotes 10–59 minutes apart can trigger a naive magnitude alarm even when both quotes are valid. An as-of, timestamp-skew-aware comparison should abstain unless observations are synchronized; a synchronous 100x discrepancy should still be quarantined. Large overlapping bid/ask spreads are a separate counterexample to midpoint-only discrepancy.

## Reproducible local prototype
Module: event_time_audit.mjs; tests: 33/33 passed. Earlier exp116+exp119 regression suites: 63/63 passed unchanged. Deterministic synthetic benchmark seed 1202026, 5000 constructed cases per scenario:
- Asynchronous legitimate jump: naive alarm 5000/5000, event-time-aware inconclusive 5000/5000.
- Synchronous 100x discrepancy: quarantine 5000/5000.
- Synchronous close quotes: consistent 5000/5000.
- Future-only observations: no-lookahead 5000/5000.
- Wide overlapping dealer spreads: inconclusive 5000/5000.

## Limits
These constructed tests are not measured market false-alarm rates. Different declared provider lineages do not prove independence. Two identically mislabelled feeds can pass. Synchronous market disagreement is not automatically a unit error. The current gold app uses daily history and one live quote, not two independently timestamped spot feeds; no deployment is justified without real provider schema/provenance validation.

## Local artifact
khepri_experiment120_bundle.zip; SHA256 0c7283762190fcad0e55482dbc22f0c1daf3e9bd9d60ebf88e31affe3b781d22. This report does not imply the code bundle was uploaded to GitHub.

## Proposed follow-up
Build a mock provider adapter and integration test that marks intraday-versus-daily-close comparisons temporally inconclusive, preserving existing freshness/mode guards.