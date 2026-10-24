# Khepri experiment 410 — point-in-time feature provenance is order-sensitive

Date: 2026-10-24. Independent research, no production changes.

## Question

Can the current `products/gold-forecast/feature-store.mjs` return different provenance (or a different serialized result) for the same set of point-in-time macro records, solely because the input order changes?

## Source fidelity

The `feature-store.mjs` and `historical-integrity.mjs` files in this experiment are exact snapshots from `main`, verified against Git blob hashes:

- `feature-store.mjs`: `7d0213edcc264b3ca79e3474aa82c2d88b434b1b`
- `historical-integrity.mjs`: `d104548e8f514903b9f7c91b3899033a85e3a914`

These are research snapshots, not edits to the upstream modules.

## Reproducible counterexamples

1. **Equal-value source tie**: two records for `yield` have identical observation and availability instants and the same numeric value, but distinct `source`/`vintage`. Upstream chooses whichever record appears first. Reversing the array changes the returned source with no warning. This is a *provenance ambiguity*, not a wrong numeric forecast.
2. **Distinct feature order**: two different features returned by upstream have different JSON key order when the input array is reversed. This matters to consumers hashing raw `JSON.stringify` output; it does not change the feature values.
3. **Equivalent timezone strings**: identical instants expressed as `Z` and `+02:00` are accepted upstream, but the chosen raw timestamp string depends on record order.
4. **Control**: a later, uniquely ranked, already-published revision is correctly selected upstream regardless of order. The experiment does not claim the whole point-in-time gate is broken.

The standalone `provenance_guard.mjs` fails closed on top-ranked ties with distinct source/vintage/value, normalizes timestamp representations, sorts output keys, and uses `Object.fromEntries` to safely retain unusual keys. It accepts exact duplicate records and genuine later revisions. Unknown metadata fields are rejected rather than silently discarded. It is deliberately *not* integrated into production.

## Results

Run: `node --test test_provenance_guard.mjs && node benchmark.mjs` with Node >=22.

- 16/16 unit tests passed.
- 8,000 seeded synthetic paired-order checks, 2,000 per case.
- Equal-value gold source ties: upstream serialized output changed in 2,000/2,000, guard rejected both orders in 2,000/2,000.
- Distinct SEO features: upstream serialized output changed in 2,000/2,000, guard stable in 2,000/2,000.
- Equivalent timestamp aliases: upstream serialized output changed in 2,000/2,000, guard stable in 2,000/2,000.
- Matured SEO revision control: both upstream and guard stable and chose latest value in 2,000/2,000.

The 100% rates arise from *constructed counterexample pairs with their reverse*, not from randomly sampled production feeds. They must not be interpreted as empirical failure rates.

## Limitations and challenge

- Source/vintage labels are untrusted strings. Neither upstream nor this guard authenticates release provenance or proves that `availableAt` is truthful.
- The guard chooses rejection instead of arbitrary source precedence. Real feeds can have legitimate equal-time, equal-value duplicates across sources, so this strict policy could reduce availability. A deployment would need an explicit source-priority contract or a conflict-resolution protocol.
- Exact JSON serialization is only stable for the defined six-field schema; this prototype rejects unknown metadata. It does not implement cross-language canonical JSON, and arbitrary future schema evolution needs explicit handling.
- It does not test forecast skill, financial data accuracy, or live provider behavior.
- The problem is primarily audit reproducibility and source attribution; the tested equal-value tie does not alter numeric features. Do not call it proof of lookahead leakage.

## Transferable lesson

A point-in-time data join needs a *tie policy* and deterministic serialization in addition to availability timestamps. Testing set permutations and semantic timestamp aliases reveals defects that chronological-only tests miss.
