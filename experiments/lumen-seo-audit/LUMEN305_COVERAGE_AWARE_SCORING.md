# Lumen 305 — Coverage-aware SEO scoring

Date: 2026-10-21. Authorized AI Agent Lab. **Synthetic offline experiment only**.

## Finding
A scorer reporting recall only on pages an auditor chooses to answer can reward abstention. In a 10-page synthetic cohort, every page has one independently predeclared `NOINDEX/warning` label.

| Metric | Selective A | Broad B |
|---|---:|---:|
| Pages answered | 1/10 | 10/10 |
| Conditional precision | 100% | 100% |
| Conditional recall on answered pages | 100% | 80% |
| Eligible-page coverage | 10% | 100% |
| **Operational recall over all eligible gold findings** | **10%** | **80%** |
| Strict exact-page rate over all eligible pages | 10% | 80% |

**Ranking reversal:** A looks better on conditional recall, but B returns 8x as many known findings.

## Tested correction
An offline Lumen305 scorer preserves Lumen304 conditional metrics and adds `eligible_gold_findings`, `scored_gold_findings`, `unscored_gold_findings`, `gold_finding_coverage`, `operational_recall = tp / eligible_gold_findings`, `selective_exact_page_rate`, `strict_exact_page_rate`, and `missed_or_unreturned_gold_findings = fn + unscored_gold_findings`. Missing/abstained eligible pages count as not delivered; unreviewed pages remain excluded. Zero-denominator ratios are null. All metrics also appear per provenance kind.

**Verified locally:** 37/37 pytest cases pass (31 legacy plus six new). Re-extracted ZIP integrity checked and 37/37 passed again. Artifact SHA-256: `634d230a1e7b91f8dbb69c18a2c9c97a1ad05be0e9283385da411a20911e72d7`.

## Limitations and recovery
- No real website, production data, or search-engine indexing was tested.
- Reviewer agreement is not proof of label correctness, independence, or capture permission.
- Operational recall measures the **delivery policy** (no returned finding = not detected), not intrinsic model capability.
- The runnable code/tests are in the local conversation artifact `lumen305_coverage_aware_scoring.zip`; this report does **not** claim the code was committed to GitHub.
- Next: test correlated cohorts and missing labels; use permissioned blind-reviewed real captures only when actually available.

**Decision:** never promote an SEO auditor on conditional precision/recall alone. Require coverage and an explicit abstention policy.
