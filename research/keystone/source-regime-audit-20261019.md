# Source-regime audit (2026-10-19)

Standard Bullion's Gold Price API documentation distinguishes recent dealer-feed captured daily closes from older LBMA/USGS-sourced prices. The exact cutover date and per-row price-side/cutoff metadata are not established. See https://standardbullion.com/gold-price-api .

The existing daily price validator only warns on >25% jumps and cannot detect a plausible 1% measurement splice. A synthetic 240-row flat-price series with a hypothetical 1% step produces 1, 7, and 30 spurious nonzero returns across horizons 1, 7, and 30 respectively. These are not real vendor observations.

Before claiming homogeneous retrospective performance: verify the source regime boundary, instrument, quote side, close cutoff, revisions and publication timing. Do not promote models or infer predictive skill from this audit. No production code changed.
