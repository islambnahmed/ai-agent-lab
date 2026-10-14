# Khepri experiment 179 — macro cutoff must not exceed verified price-close time

Date: 2026-10-14. Experimental branch only; production unchanged.

## Reproducible finding

In `products/gold-forecast/scripts/evaluate_research.mjs` (main blob `90788bec6c3631b8343738531ae3ddfad1238b7d`), macro context is constructed with `series[i].date+'T23:59:59.999Z'`. The price series contains UTC date and daily last M1 bid price, but not the exact timestamp of that day's last M1 quote. `feature-store.mjs` correctly enforces `availableAt <= origin` against this *assumed* end-of-day origin.

Counterexample: a gold close at 2026-10-12T16:00:00Z and a macro release at 2026-10-12T20:00:00Z. Existing EOD join admits the post-close macro value; a true 16:00 join excludes it. Therefore there is a **potential look-ahead exposure**, not verified real-data leakage.

## Evidence and transfer

A local Node 22 prototype passed 9/9 tests: after-close counterexample; conservative unknown-close gate; exact timestamp gate; equivalent timezone offsets; invalid timestamps; prior-day edge; environmental-sensor transfer; 500-origin adversarial simulation; and a competing case where conservative gating unnecessarily excludes valid pre-close releases. In the deliberately adversarial synthetic case, EOD admits the 500 post-close signals; conservative gate admits none. This is not a market performance estimate.

## Proposed fail-closed contract

- If a trustworthy price-close instant exists, use it for macro feature availability.
- If only a UTC price date exists, use 23:59:59.999Z **on the previous date** as a conservative cutoff. This may underuse legitimate same-day macro releases.
- Preserve original M1 quote timestamps through the daily aggregator to restore same-day information safely.
- Recompute metrics only after timestamp provenance is available; do not promote models based on current inspected audit.

The tested standalone `close-gate.mjs` and tests are retained in the local reproducible experiment archive. Main, live forecast selector, and existing historical reports were not changed. Raw vendor archives and full repository CI were not run.
