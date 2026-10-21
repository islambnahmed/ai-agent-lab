# Worker A cycle 269 — Lineage-aware quote corroboration (research-only)

Date: 2026-10-21. This is a synthetic, offline experiment; **no live gold data or provider independence was verified**.

## Problem and approach

Cycle 268 showed that a three-of-five provider majority can be entirely wrong when three feeds copy one upstream. A separate failure arises when missing providers silently reduce the denominator. The new `products/gold-forecast/lineage-consensus.mjs` prototype counts one vote per *declared audited upstream root*, not one vote per publisher.

The API is `assessLineageConsensus(quotes, roster, {originAt, maxAgeMs, tolerance, minIndependentRoots, minRosterCoverage})`. It:
- requires a fixed expected provider roster, a lineage root, a nonempty evidence reference, and an audit timestamp no later than the evaluation origin;
- rejects future, stale, duplicate, invalid, or convention-mismatched quotes;
- quarantines conflicting quotes from the same root, and abstains when eligible feeds use mixed quote conventions;
- requires both roster coverage and distinct-root quorum;
- abstains on ambiguous best price clusters rather than arbitrarily picking a winner;
- returns `corroborated_quotes` or `insufficient_evidence` with explicit reasons. **Corroboration is not a claim that a price jump is genuine.**

## Reproducibility and findings

Fourteen local Node 22 regression tests passed on 2026-10-21. Cases included common-upstream majorities, denominator collapse, future audit evidence, stale/future quotes, duplicate providers, conflicting same-root quotes, mixed conventions, ties, order invariance, and invalid inputs. The first run found a test expectation mismatch (coverage abstention took precedence over root count); corrected the test. A second code review found that conflicting-root providers could inflate coverage; excluded them from the final coverage numerator before the successful test run.

Synthetic examples:
- Five agreeing feeds with five declared audited roots: corroborated.
- Three bad feeds sharing one declared root, plus two independent normal feeds: abstains (only two agreeing normal roots; the three bad feeds count as one root).
- Two agreeing bad feeds and three missing expected feeds: abstains (2/5 roster coverage).
- **Known unresolved counterexample:** three bad feeds with three *falsely distinct* root labels are still corroborated. A string field or nonempty `evidenceRef` does not verify independence.

## Deployment status and next evidence

The research module was published on `sandbox/worker-a-20261021-lineage-evidence-gate` at commit `6b15415fe790103f9d0214a54bec05dcc15fa2aa`. Uploading the new regression test file was blocked by platform safety checks. The 14 tests therefore ran **locally only**; no repository CI success is claimed for this module. No changes to `main`, trading logic, or production forecasting.

Before any integration, independently inspect and version acquisition-chain evidence, record the roster as-of each origin, verify quote conventions and upstream independence, and test on held-out legally obtained multi-provider gold observations. Preserve the counterexample where false provenance defeats the gate. Do not equate synthetic pass rates with market reliability.

## Additional deterministic stress test and CI status

A separate seeded synthetic check ran 1,000 trials per scenario with small quote jitter:
- Five genuinely distinct *declared* roots with matching prices: 1,000/1,000 corroborated.
- Three erroneous feeds correctly mapped to one shared root, plus two normal roots: 1,000/1,000 abstained.
- Three erroneous feeds incorrectly labelled as three distinct roots: 1,000/1,000 **falsely corroborated**.

These are controlled synthetic outcomes, not real-world performance rates. The new code commit passed Gold Lab MVP tests (run 39543651304) and AI Agent Lab CI (run 39543651423), but the blocked new regression file is **not part of those CI runs**. Local tests and stress script remain in the recovery bundle.
