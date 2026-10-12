# Worker A — Cycle 73: exact-repository parity for scalable gold backtest (2026-10-12)

## Material improvement over cycle 72
Cycle 72 compared the fast engine to a reconstructed stand-in. This cycle fetched the **actual** branch files from this repository and independently confirmed their Git blob identities locally:
- `walkforward-benchmark.mjs` SHA `bb07e9412ff3bc690d7eb39d99046a930cece427`
- `quote-core.mjs` SHA `5cd92158486ee7516ca42249e090540032203bac`

The cycle-72 `walkforward-scalable.mjs` candidate was run against these exact modules, not a stand-in. Tests compared the entire output including summary, skip counts, all forecasts and metadata, excluding only deliberately different caveat prose.

## Reproduced tests
- 500 seeded datasets with delayed/out-of-order captures, gaps, simultaneous capture times, provenance and both horizon anchors.
- 2,000-row synthetic replay with a strict 75-minute issuance-anchored target.
- Equal-capture batch edge case.
- Matching errors for invalid options, price, and mixed source.
- Eight previous candidate tests, including 100,000 synthetic rows.
- **12/12 tests passed** on local Node.js v22.16.0.
- Original vs fast on identical 6,000-row synthetic data: **553.17 ms vs 44.42 ms**, ~**12.45x** faster in one run, same 5,962 forecasts and same MAEs.
- 100,000-row synthetic candidate run: about **789 ms** in this test run.

## Interpretation and limits
This resolves the exact-source parity gap from cycle 72 on the tested cases. It does **not** prove complete equivalence for every possible input, market-data provenance, forecast skill, or reproducible performance on other machines. Timing measurements are single-run, noisy and not production guarantees. The 100,000 rows are synthetic and are **not** real gold predictions.

The candidate should remain a reversible alternative until its implementation and tests are published and reviewed. Next highest-value step is to obtain a longer, documented market series with explicit candle-close availability and independently verifiable as-of capture evidence, then compare genuine prospective forecasts against persistence.

## Reproduce locally
Place `walkforward-scalable.mjs` from cycle 72 beside the two exact-SHA repository modules. Run `node --test walkforward-scalable.test.mjs walkforward-scalable.repo-parity.test.mjs` and `node cycle73-perf.mjs`.

Local cycle-73 artifact includes tests, performance JSON, original SHA-matched modules and the candidate. Do not treat this report as proof of a GitHub code commit unless each code file has been read back.
