# Keystone — reversible cross-root integration candidate (2026-10-25)

## Purpose
Test whether three independently developed offline research capabilities can coexist on one exact Git tree without losing regression coverage. This is an **integration candidate, not a release**. No merge to main, deployment, client data, live crawl, or trading.

## Provenance (immutable source commit SHAs)
- Offline redirect-map audit and retirement coverage (root #40, leaf #48): `178880c6deef03acf5a00e3b1568b6f0ddd2aa8d`; chosen as parent of this candidate.
- Offline sitemap audit/diff/triage/field scorer (consolidated #34 and leaf #38): `b9ac4d349f463325929502ec933ec256b6f3cdfe`; copy **17** added file blobs, including the separate sitemap CI workflow.
- Gold walk-forward numerical guards (draft #55): `79f63ad2df2c78979a5402a36d33694fab755a4a`; copy **2** existing-file replacements (tool and test).

## Verified pre-integration structural evidence
- GitHub compare from `main` showed **no file-path overlap** between redirect and sitemap source changes, nor between those and gold tool/test *changes*.
- Redirect and gold roots **both modify** `.github/workflows/ci.yml`; a naive whole-file copy of either branch would silently drop the other branch's test step(s). This candidate explicitly retains lab validation + **two redirect suites + gold walk-forward suite**. Sitemap has its own independent `.github/workflows/seo-sitemap-audit.yml` running six suites.
- All 19 copied source blobs are unmodified from the named source commits. Only the shared CI file and this report are newly composed.
- Parent is redirect leaf #48, so redirect history is preserved; sitemap/gold file contents are imported as blobs, not cherry-picked commit ancestry.

## Reproducibility / review gates
1. Compare this branch against `main` and source heads; confirm all expected paths and blob SHAs.
2. Check GitHub Actions on **this exact candidate commit**: `AI Agent Lab CI` and `Offline SEO sitemap audit tests`; inspect failed steps, not just summary badges.
3. Run local/CI synthetic tests and investigate any failures before calling the candidate integrated.
4. Independent security/privacy and input/output safety review remains required. Field evidence and customer-authorized samples are **not available**; no SEO uplift or predictive skill can be claimed.
5. Review/retire the original draft stacks deliberately; **do not auto-merge** this candidate or treat the backlog as production releases.

## Scope limits
This artifact is an integration experiment and recovery checkpoint. It does not grant permission to alter security settings, secrets, external services, or `main`.
