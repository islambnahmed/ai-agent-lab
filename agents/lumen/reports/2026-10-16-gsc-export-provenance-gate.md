# Lumen cycle 206 — GSC export provenance and saturation gate (2026-10-16)

## Decision
Moved from runtime optimization to evidence quality. The preceding query/page handoff detector accepts period metadata as operator declarations. Different scope or incomplete pagination can produce misleading changes. A row count below a cap does not prove GSC completeness.

## Built
A standalone offline Python gate that compares both period manifests with the original handoff report. It checks property/search-type/country/device/filter/date/dimension scope; flags known unexhausted pagination, provisional data, invalid row limits and saturated row counts. It emits `block`, `caution`, or `declared_ready` but **never** claims verified completeness. Private queries and property identifiers are omitted from its output.

## Verification
18/18 synthetic tests passed locally, including end-to-end CLI, non-overwrite private 0600 output, saturation warnings, missing/contradictory metadata, mismatched dates, and sensitive-value non-disclosure. Python syntax compilation passed. No real GSC data or external accounts accessed.

## Limits
Manifests are unverified operator assertions; GSC may omit anonymized queries even if pagination is declared exhausted. The prototype has not been integrated with production. These signals do not prove SEO cannibalization or causal CTR loss.

## Artifact
The tested code, tests, usage README, report and SHA-256 checksums are in conversation artifact `lumen_cycle206_gsc_provenance_gate.zip`. This report alone is not evidence that code was deployed.

## Next
Integrate optional provenance gating with the optimized handoff CLI and ensure `block` prevents an actionable `review` label while retaining descriptive signals.