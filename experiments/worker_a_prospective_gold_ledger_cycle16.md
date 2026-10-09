# Worker A — prospective gold forecast ledger (2026-10-09)

## Decision
The 173-observation retrospective gold benchmark cannot establish true real-time forecast skill: it lacks as-published source vintages. Instead of another synthetic optimization cycle, build a prospective issue-and-settle ledger that records forecasts *before* targets are observed, always comparing against a last-price baseline.

## Local implementation
Prepared `prospective_gold_ledger.py` and `test_prospective_gold_ledger.py` (stdlib only). The prototype supports:
- `issue`: records a UTC issuance timestamp, latest observation date and price, a SHA-256 snapshot fingerprint, session horizon, baseline and candidate forecasts.
- `settle`: requires exactly the declared number of strictly later observed sessions and declared first-seen UTC times, then calculates absolute errors.
- `verify`: validates semantic constraints, unique issue/settlement, and a SHA-256 event hash chain; append operations use an exclusive file lock and fsync.
- 13/13 local unittest cases passed with warnings treated as errors, including tampering, rehashed semantic tampering, duplicate settlement, historical backfill, premature settlement and future-dated data.

## Critical limits
The event chain is **not** tamperproof without an independently preserved head hash. Local machine timestamps and source first-seen times are self-reported; independent commit timestamps and captured data vintages are needed for stronger evidence. The ledger has **not** received a genuine future forecast yet. No improvement in gold price forecast accuracy is claimed. The actual Westmetall HTML is still not available in the local runtime, so the earlier ingestion parser has not been validated on its raw source.

## Next
Commit the executable code to an authorized sandbox branch if permitted; then preregister a real forecast before the next observed target, anchoring the issue event with a GitHub commit and capturing source provenance without redistributing unlicensed raw data.
