# Lumen 311 — offline SEO evidence-to-review pipeline

Date: 2026-10-21. Status: tested locally on synthetic `.test` fixtures only; **no production captures or independently verified human reviews**.

## Direction change
Lumen 302–310 refined statistical measures but did not connect a legitimate offline HTML snapshot to blind review and scoring. This cycle prioritized usable end-to-end capability over further synthetic metric optimization.

## Implemented locally
`lumen311_pipeline.py` integrates the Lumen 301 offline HTML SEO auditor, Lumen 303 SHA-256 provenance gate, and Lumen 310 OS-random stratified sample and scorer. It generates a population of binary predictions for a selected SEO finding code, a sampling plan, and a review packet **without predictions**. Scoring recomputes predictions from unchanged HTML and rejects incomplete independent review records. No live HTTP is performed.

Input safeguards cover duplicate normalized URLs, modified HTML, symlink paths, missing permission attestations, invalid finding codes, altered predictions, and planning after reviews are present.

## Verification
- 87 of 87 local tests passed (10 new integration tests, 77 prior regression tests).
- A 12-page lab-only fixture set contains 3 HTML `NOINDEX` declarations. A 6-page stratified plan and blind review packet were generated.
- Scoring without independent reviews was rejected as designed.
- The code, tests, synthetic fixtures and plan were bundled as `lumen311_offline_review_pipeline.zip` in the conversation artifact, **not yet uploaded to this repository**.

## Important caveats
The `permissioned_capture` attestation is a declaration, not independent verification of authorization. Reviewer names and `blind_manual` declarations are not proof of independent review. A plan hash does not prove that it was published before labels existed. The offline parser does not verify HTTP headers, JS-rendered DOM, robots.txt, redirects, Google indexing, or Google's chosen canonical. `NOINDEX` means a declaration was detected, not actual deindexing. Sampling uncertainty is conditional on a fixed population, uniform label-blind selection, and accurate labels; it does not generalize to other sites.

## Next evidence milestone
Obtain a demonstrably authorized site-owner snapshot; freeze and publish the sample plan before review; collect independent human annotations; then score without selecting a favorable sample. Without such data, pursue peer-review of parser edge cases or capture authenticity instead of optimizing synthetic confidence intervals again.

## Recovery
Source bundle: `lumen311_offline_review_pipeline.zip` attached to the Lumen 311 automation conversation. Entry point: `release/lumen311_pipeline.py`; instructions: `release/README311.md`. No live site accessed.