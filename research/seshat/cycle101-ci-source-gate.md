# Seshat cycle 101 — CI integration and real-source qualification (2026-10-12)

## Verified change
- Base: `seshat/cycle100-integrate-audits-20261012`; isolated successor: `seshat/cycle101-integrate-research-audits-20261012`.
- Extended `.github/workflows/gold-lab.yml` to syntax-check the prospective ledger and run `research/prospective_ledger.test.mjs` in CI. The existing forecast test command did **not** cover that file.
- Commit: `fc0aa31bf560ba26dad71c75fb76c0c215fea978`.
- At initial verification, Gold Lab CI was queued, **not yet passing**. Do not report green until the workflow completes.

## Real-data gate — negative evidence, not a forecast
- GoldPrice.com advertises historical daily XAU/USD closes as `date,close`, with attribution permitted, at https://www.goldprice.com/gold-price-history .
- Its current page shows a series ending `2026-10-10`, a Saturday; it also reports 2026 year close `$4,194.65`. Weekend-dated observations require manual provenance investigation before using them as a trading session. Do not silently remove or reinterpret them.
- A second site, https://goldprice.dev/gold-price-history , reports the last close `2026-10-09` at `$4,194.81`. These sites differ in dates and quote methodology; a 16-cent difference is **not** enough to establish which is authoritative.
- The CSV link `https://www.goldprice.com/gold-price-history.csv` was exposed but not retrievable by the available browser/text downloader (unsupported text/csv). The container's network DNS also failed. Thus **no authenticated historical dataset was ingested** in this cycle.
- FreeGoldAPI https://freegoldapi.com/data/latest.json was accessible in the research browser but its last displayed observation was `2026-02-20`, stale by over seven months. It cannot be the current origin close.

## Decision
Do not manufacture a live forecast from a webpage summary, a stale series, or a weekend-labelled close. Obtain a complete CSV with source, retrieval timestamp and checksums; audit the session calendar and cross-source close convention; then freeze model revision and commit a pre-outcome receipt. Preserve all pending receipts and publish settlement errors later.

## Local experiment
Previously saved `seshat_cycle99_cohort_audit_2026-10-12.zip` was extracted and its 67 research tests passed with Node 22 locally. Those research modules are **not yet part of this GitHub branch**; their local result must not be described as GitHub CI coverage.

## Next useful step
Get GitHub CI green for the 21 prospective ledger tests, then integrate and CI-test the separately audited snapshot/replay/cohort modules, or switch provider if daily closes remain inaccessible. Do not merge into main until evidence is complete and concurrent changes are reviewed.
