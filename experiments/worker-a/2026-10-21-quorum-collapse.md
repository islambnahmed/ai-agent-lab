# Worker A cycle 268 — Quorum collapse and correlated-feed counterexamples

Date: 2026-10-21. Offline synthetic research only; no live gold data, trading, or production integration.

## Method
Reused the unmodified cycle267 local jump-provenance triage implementation. Deterministic five-provider scenarios with 100 seeds (3000–3099), 8% price jump, and small independent quote jitter. Compared the original prototype with an experimental static-roster gate requiring >=3 agreeing sources and >=60% synchronized roster coverage. Eight local Node.js tests passed; no GitHub CI run is claimed.

| Scenario (100 synthetic seeds) | Original | Configured quorum |
|---|---|---|
| True jump, five feeds agree | 100 corroborated | 100 corroborated |
| One bad feed, four normal | 100 suspected bad tick | 100 suspected bad tick |
| Two correlated bad feeds, three normal | 100 suspected bad tick | 100 suspected bad tick |
| Three correlated bad feeds, two normal | 100 **falsely corroborated** | 100 **falsely corroborated** |
| Four correlated bad feeds, one normal | 100 **falsely corroborated** | 100 **falsely corroborated** |
| Three stale feeds, two remaining correlated bad feeds | 100 **falsely corroborated** | 100 **insufficient evidence** |

## Findings
**Quorum collapse:** The original strict-majority denominator silently shrinks to currently eligible feeds. When three of five configured providers become stale, two correlated bad feeds can produce a corroborated_jump result. An explicit roster/coverage requirement makes this specific case abstain.

**Common-mode limitation:** A 3-of-5 majority of nominally distinct provider groups sharing one bad upstream feed still gets falsely corroborated. Declared independence labels do not prove real independence. Price agreement alone cannot always distinguish a genuine jump from correlated data corruption. Even an absolute quorum cannot resolve this without separately verified provenance or an external oracle.

## Decision
Keep source triage research-only and separate it from the volatility detector and any trading decision. Before integration: require an audited, point-in-time provider roster; acquisition-lineage evidence; quote-convention matching (spot/futures, venue, bid/ask/mid, currency, session); and held-out authorized multi-provider observations. Evaluate event-level false alarms and duration rather than only per-origin alarms.

**Caveat:** All counts are controlled synthetic scenario outcomes, not real-world false-positive estimates or evidence of forecast skill.

Local reproducibility artifacts (benchmark, tests, JSON output, unchanged cycle267 module, checksums) are preserved in cycle268 recovery bundle. No main-branch changes.