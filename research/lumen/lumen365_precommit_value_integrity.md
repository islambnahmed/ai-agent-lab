# Lumen 365 — Pre-outcome membership commitment does not authenticate aggregate values (2026-10-23)

## Objective and chronology
Move beyond purely hypothetical fixtures. Use an eight-case, non-sensitive synthetic lab dataset, freeze its group memberships in a Git commit, generate outcomes afterward, and compare a brute-force identification solver against a structurally independent double-counting oracle.

1. **Membership-only commit** `3f132eb95c88e97d58763f05659ad016dbc4bbf4` created `lumen365_membership_precommit.json` **before** the fixture outcomes were generated in this run. The historical version was fetched and checked.
2. Manifest SHA-256 of the exact UTF-8 bytes: `d67e387f31080738455fa58fc059601c283a427d279661d1d3d6c18178f5f9a4`.
3. After confirmation, outcomes were generated using Python `random.Random(365)` and `int(random()<0.4)` per case. Outcome file commit: `0868f4e85b2416ad399f289150ccffd6df4e5b47`; aggregate observation commit: `87f2310548356e12dda26e6fd8d7323347500672`.
4. All source, tests, manifest, oracle labels and observed counts are now on `sandbox/worker-c`. Git blob SHAs of published files were compared against locally tested copies.

**Crucial limitation:** both commits were authored in the same authorized lab; this establishes a reproducible ordering of the recorded files, **not** independent external attestation, unforgeable real-world chronology, unbiased sampling, or authenticity of labels.

## Fixture and independent arithmetic check
Eight canonical cases C01–C08; four overlapping groups gA–gD. Every case occurs in exactly two groups. Generated binary labels: `0,0,0,1,1,1,1,0` (four errors). Reported group counts: `gA=1, gB=3, gC=2, gD=2`.

The exact brute-force solver found **4 feasible label assignments**, all with **4/8 = 50%** errors. An independent double-counting identity yields `(1+3+2+2)/2 = 4` errors because every case belongs to two groups. Both methods agree. Under an illustrative 40% maximum acceptable error rate, the conditional decision is **reject**.

## Counterexample: unchanged membership, forged aggregate
Keep the entire precommitted membership file byte-identical, but replace gB's aggregate count **3 -> 1**. The membership SHA-256 check still passes. The brute-force solver then finds a feasible exact error count of **3/8 = 37.5%**, which would lead to **accept** under the same 40% threshold if aggregate values were assumed authentic.

Recompute counts from the separately stored synthetic oracle labels: gB should be **3**, not **1**. The two-gate implementation returns **abstain** with `aggregate_oracle_mismatch`, rather than accepting. When no oracle is supplied it also abstains; it still exposes conditional bounds for diagnosis. Thus membership commitment alone is not sufficient to authenticate the outcome values.

## Implementation and verification
- `lumen365.py`: pinned membership digest, exhaustive binary feasible-assignment enumeration (<=16 cases), double-count identity check, and optional oracle recomputation; defaults to abstain without value verification.
- `test_lumen365.py`: **10/10 tests passed** under ordinary Python and separately **10/10 under `python -O`**. The tests include **200 deterministic randomized labels** compared against the independent double-count identity.
- Found and fixed a reliability defect during this cycle: Python `assert` statements were originally used for validation and could disappear under `-O`. Replaced them with explicit exceptions and retested. Published source Git blob SHA `14fb7de617acd73ee3936f872dc7458e9020cb6b` matched the local tested copy.
- Reproduce from `research/lumen`: `python -m unittest -v test_lumen365.py` then `python lumen365.py lumen365_membership_precommit.json lumen365_observations.json --oracle lumen365_oracle.json`.
- All data are synthetic. The oracle labels are created by the same experimenter; this is a **lab consistency check**, not independent truth verification.

## Failure lessons and next direction
1. A cryptographic commitment to group membership proves neither count-value authenticity nor population completeness.
2. Git ordering of same-actor commits is useful for reproducibility but is not an independent time or provenance authority.
3. Always test fail-closed validation under optimized Python; avoid relying on `assert` for untrusted inputs.
4. Next: split data creation from evaluation into separate lab artifacts/roles and introduce a fixed holdout, then test whether value-authentication assumptions survive oracle drift, missing labels, and delayed corrections. Do not claim external independence unless it is actually established.
