# Worker A — Same-day target settlement guard (2026-10-18)

Scope: `products/gold-forecast/journal.mjs` on main. This is a reproducible synthetic audit, not evidence of a real-world leaked gold fixing.

The current settlement predicate `targetDate < receipt.issuedAt.slice(0,10)` accepts a target whose UTC calendar date equals the issuance UTC calendar date. An illustrative one-close-ahead receipt issued 2025-09-18 23:00Z with targetDate 2025-09-18 can be marked `matured` later without proof that the target price was unavailable at issuance. A hash is not proof of publication timing.

A naive change to reject same-day targets at issuance is **wrong**: for daily histories that exclude the current UTC day, it would suppress nearly every horizon-1 research forecast. Keep issuance available; quarantine same-day settlement until provider-specific release evidence is independently authenticated. Conservative proposed settlement predicate: `targetDate <= new Date(parseInstant(receipt.issuedAt)).toISOString().slice(0,10)` => quarantine.

Local isolated harness used a faithful copy of journal.mjs with deterministic mocked forecast/history helpers; 5/5 tests passed after revising the overstrict proposal. This is not a full-repository test or GitHub CI result. No production change is claimed.

Next: run the actual gold test suite on a main-based sandbox branch and add an evidence-backed provider publication contract before scoring same-day outcomes.
