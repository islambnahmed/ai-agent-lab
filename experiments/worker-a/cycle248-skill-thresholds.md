# Worker A cycle 248 — falsifiable gold-forecast skill thresholds (2026-10-20)

## Why this direction
The preceding cycles built increasingly strict synthetic provenance gates but lacked independently authenticated target closes. Instead of another simulated gate, this cycle extracts **deterministic, pre-outcome conditions** from the three existing real forecast receipts in `products/gold-forecast/reports/prospective/`.

## Verified inputs
All three receipt JSON bodies match their stored SHA-256 identifiers under the repository's `JSON.stringify` convention (property insertion order matters). Origin close / persistence baseline: **4207.98 USD per troy ounce**. Receipt issuance: **2026-10-12T17:12:52.272Z**. No target outcomes or target-close publication timestamps were independently verified.

## Mathematical certificate
For a point forecast P, persistence baseline B and actual future close Y, compare absolute errors `|P-Y|` versus `|B-Y|`.
- If P = B, both errors are **identical for every Y**. Strict outperformance is impossible.
- If P > B, the forecast wins **if and only if Y > (P+B)/2**.
- If P < B, the forecast wins **if and only if Y < (P+B)/2**.
- At equality of Y and midpoint the models tie. The difference in absolute errors is always bounded by `|P-B|` (triangle inequality).

| Horizon | Model | Forecast P | Baseline B | Strictly better than baseline iff | Maximum possible per-case absolute-error advantage |
| --- | --- | ---: | ---: | --- | ---: |
| 1 observed close | persistence | 4207.9800 | 4207.9800 | **Never** | $0.0000/oz |
| 7 observed closes | mean_reversion | 4225.4834 | 4207.9800 | **Y > 4216.7317124** | $17.5034/oz |
| 30 observed closes | momentum | 4183.9581 | 4207.9800 | **Y < 4195.9690656** | $24.0219/oz |

These are pre-outcome conditions, **not** realized wins or trading signals. The h1 receipt cannot provide evidence of beating its persistence baseline by MAE because it is the baseline itself. One outcome per horizon cannot establish statistical predictive skill. No mixing horizons.

## Execution and checks
Created a dependency-free Node module `experiments/worker-a/skill-threshold-certificates.mjs` on `sandbox/worker-a-20261020-skill-threshold-certificates`. It validates receipt hashes, rejects invalid values, and emits certificates without scoring unverified outcomes. Re-read the published file and confirmed its presence.

Local regression suite: **7/7 tests passed**, including 3 original receipt hash validations, 3 tampering rejection cases, invalid realized prices, exact tie points, and 2,000 deterministic price probes across h7/h30. The test source was **not published**: the GitHub test-file write was blocked by platform safety checks; no bypass attempted. Local recovery copy is available separately. `main` and CI were not touched.

## Durable lesson
Receipt hashes are over `JSON.stringify(payload)`, not canonicalized JSON: reconstructing a receipt with identical values but different object-key order initially failed the hash test. Preserving original field order resolved the failure. This is a serialization contract worth documenting.

## Next direction
Obtain independently attested completed provider closes and publication times, then apply the frozen thresholds without post-hoc model changes. If unavailable, pursue a distinct lab capability rather than building more simulated provenance gates.
