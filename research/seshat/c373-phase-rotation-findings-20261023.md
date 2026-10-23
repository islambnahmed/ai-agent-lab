# Seshat C373 — phase-rotation findings (2026-10-23)

## Evidence anchors
- Code branch: https://github.com/islambnahmed/ai-agent-lab/tree/seshat/c373-phase-rotation
- Pre-registered protocol: experiments/seshat/c373-phase-rotation/README.md, committed before live CI execution.
- GitHub Actions run: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40018127537 (completed **success**), job 120635389071, six offline tests passed and live read-only provider fetch succeeded.
- General Lab CI: https://github.com/islambnahmed/ai-agent-lab/actions/runs/40018127441 (success).
- Live fetch timestamp: **2026-10-23T20:18:03.222Z**.
- Source: Standard Bullion public 1y XAU/USD daily API. Current rolling series: **324 rows**, 2025-10-23 through 2026-10-22; cadence classified as `observations`.
- Response SHA-256: `bc6d6a15fedb65c7eb66d7e97d05bc41c58941d2a303ae1814587a681fb6436e`, **identical to C371's 2026-10-23T17:13:30.697Z retrieval**. This confirms byte-identical fetched responses in those two runs, not original 2026-10-12 vintage integrity or price accuracy.

## Results — all disjoint offsets, not a selected one

| Horizon | Selected model in current feed | Overlapping audit rows | Pooled MAE skill vs no-change | Rotated disjoint phases |
| --- | --- | ---: | ---: | --- |
| H1 | persistence | 65 | 0% | 1/1 phase ties baseline |
| H7 | mean_reversion | 59 | **−3.0630%** | **4 positive, 3 negative**; each phase n=8–9 |
| H30 | persistence | 36 | 0% | 30/30 phases tie baseline; each phase n=1–2 |

For H7, phase skill ranges from **−22.9873%** (offset 0, n=9) to **+6.9503%** (offset 4, n=8). Other offsets: 1 −18.9472%, 2 −4.0505%, 3 +6.4375%, 5 +4.5456%, 6 +2.2331%. A single disjoint offset would have conveyed a misleadingly definite story about model performance.

## Material change versus the pinned October 12 retrospective report

The earlier readiness report had H7 pooled skill −3.0560% and offset-zero disjoint MAE 115.47 (model) versus 119.28 (baseline), superficially favorable to the model. **The October 23 rolling feed's offset zero instead has −22.9873% skill**. The offset-zero samples cover different dates after the window rolls, so this is **not** proof of a historical price revision; it demonstrates why single-offset results are unstable.

The October 12 report selected **momentum** for H30 (pooled skill −14.3331%); the October 23 rolling-vintage recomputation selected **persistence** for H30 (0% by construction). This is a model-selection change under a different data window, not proof of live predictive improvement.

## Decision

- **Do not cite one rotated phase as evidence of an edge.** Report pooled and all phase signs/counts, with uncertainty.
- **Do not certify any historical prospective settlement.** Raw original issuance vintage and independent same-definition close evidence remain unavailable.
- **Stop iterating source-definition gates absent new evidence.** Next high-value work should be genuinely forward, pre-registered predictions with lawful source-vintage preservation, or an independent out-of-sample dataset with known provenance.
- This is a current-vintage *descriptive sensitivity* experiment. All 59 H7 overlapping rows are dependent; disjoint phases share regimes. No significance test or trading advice.
- No changes to main, no credentials or raw vendor feed stored.
