# Keystone — Real-gold evidence reconciliation (2026-10-16)

## Decision: stop treating synthetic drift tests as evidence of gold forecasting skill

The standalone `tools/gold_walkforward.py` and the synthetic 900-path regime stress are useful **numerical / model-behavior diagnostics**, but they are not the actual product's deployed selection procedure and do not validate live predictive skill. The product already has a materially more relevant real-provider audit in `products/gold-forecast/GAP_AUDIT.md`, `SOURCES.md`, and the frozen `reports/*-20261012.json` files. Future Keystone work should use those artifacts as the starting point rather than accumulating more synthetic-only improvements.

## Verified repository evidence

- The product's native Standard Bullion 1y snapshot had 324 **irregular observed closes** from 2025-10-12 through 2026-10-11. Horizons are *observed provider closes*, not calendar days or exchange sessions.
- The 2026-10-12 product audit reports: h1 persistence MAE 39.41 vs baseline 39.41 (0% skill, 65 disjoint target windows); h7 mean reversion MAE 122.52 vs baseline 118.88 (-3.06% skill, 9 windows); h30 momentum MAE 258.77 vs baseline 226.33 (-14.33% skill, 2 windows). These are **already-inspected retrospective outcomes**, not a fresh independent test.
- A separate HistData research archive contained 3,221 UTC daily bid closes (2016-01-03 to 2026-05-31) with documented quarantines; it is a **different measurement/source**, not a continuation of the dealer snapshot. The macro Ridge ablation did not beat matched price-only Ridge at any of h1/h7/h30 on the reported disjoint audit.
- Three product prospective receipts exist on `main` under `reports/prospective/2026-10-11-h{1,7,30}.json`. They all self-report issue time `2026-10-12T17:12:52.272Z`, source fetch `2026-10-12T17:10:55.750Z`, code commit `4caa8a445b4490e7be098b8dbf742be8e2ae0d7b`, origin close 4207.98, and `targetDate: null` because the future provider observation calendar is unknown.
- GitHub's commits-for-path API returned introduction commit `11b3026467cc26c4659f5f07d8836608d38e026f` for the h1 receipt. Its commit metadata lists `2026-10-12T17:13:52Z`, and its parent matches the pinned code commit. **Git author/committer timestamps are editable metadata, not a trusted server-side publication-time proof**. The other two receipts' independent introduction times were not checked in this cycle.

## Critical distinction: no prospective accuracy result yet

No refreshed authenticated vendor history or frozen source vintage was retrieved during this Keystone cycle. Therefore none of the three receipts was settled or counted as matured. In particular, the one-close receipt **may** have matured by 2026-10-16, but that cannot be inferred from elapsed calendar time or an indicative spot quote. It requires a subsequent *completed* observation in the same source, an unchanged historical prefix, and evidence the receipt was externally anchored before the target close.

The receipt's SHA-256 ID protects internal record integrity, not the honesty of its `issuedAt` field. A Git commit's self-reported date is not sufficient alone. The product's `journal.mjs` correctly warns that external Git timestamp anchoring is required.

## Next executable experiment (not yet performed)

1. Fetch a new **native 1y Standard Bullion history** and preserve its raw SHA-256, retrieval time, unit, cadence, and vendor contract. Never substitute HistData, Gold API spot, or an unverified daily interpolation.
2. Run the existing `scripts/journal.mjs settle` with the original ignored local `data/vintages/<historyHash>.json`; confirm prefix hashes, date integrity, and quarantine revisions. If that frozen vintage is unavailable, **fail closed** rather than reconstructing it from the report.
3. Independently verify server-observed publication before each target observation (for example, an applicable GitHub Actions run `created_at` tied to the introducing commit, if present). Keep self-reported Git commit timestamps distinct from server event timestamps.
4. Report each horizon separately as `pending`, `matured`, or `quarantined`, and preserve every receipt; no promotion or accuracy claim from one matured h1 sample.
5. Only after a genuinely untouched cohort matures, compare model and persistence MAE with dependence-aware uncertainty and explicit selection history.

## Reproducibility and safety

No production code or model selection was changed in this reconciliation. No live data was downloaded, no prospective receipt was rewritten, and no new model-performance estimate was fabricated. The earlier synthetic results remain valid only under their stated simulated assumptions. This note is a durable correction to research priorities, not a deployment or prediction.

Repository sources: `products/gold-forecast/{GAP_AUDIT.md,SOURCES.md,journal.mjs,scripts/journal.mjs,reports/prospective/*}`; `research/keystone/gold_regime_stress_20261016.md` on `sandbox/worker-b-gold-tests-ci-20261016`.
