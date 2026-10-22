# Lumen 342 — publish prospective-claim screening code (2026-10-22)

## Result
Published the independent, fail-closed Python screening utility on `sandbox/worker-c` at `research/lumen/cycle342_prospective_claim_gate.py`, commit `04d608dec9cc3d4a0fb8a7e2dbafa8c697c7ec43`. Retrieved the committed blob and verified its Git blob SHA is `1b063ca3aa2dc62dc42767dae769e6c75fea2b70`. The locally tested file's Git blob SHA matched that value exactly.

## New false-positive cases closed
1. A receipt cannot use an origin date that has not completed its UTC day when issued.
2. A target claimed as a completed UTC-day close cannot be marked published within the same UTC day. This is deliberately conservative: it is **not** a verified Standard Bullion publication schedule.
3. For irregular observed-close horizons, the evidence must explicitly attest to independently verified sequence completeness; seven supplied rows alone do not prove there were no omitted provider observations.

The utility also screens anchor ordering, provider/unit/grain, vintage, exact observation count, monotone dates, positive finite prices, and first-availability provenance. It computes errors only if all required evidence flags are supplied. **It does not authenticate those flags or fetch vendor data.**

## Tests and proof gaps
16/16 local Python unittest cases passed against a local file whose Git blob SHA matched the published file. The test suite could not be published to GitHub (write rejected), so no GitHub CI success is claimed. A demonstration using the October 12 h1 receipt metadata and no independently verified vendor outcome returned `insufficient_evidence`. No provider-matched settlement or predictive skill is claimed.

The source endpoint was not retrievable in this run; the public vendor contract says its daily close is derived from the day's last captured price, without publishing an independently verified first-availability timestamp for the relevant historical targets.

## Reproduce
From repository root:
`python3 research/lumen/cycle342_prospective_claim_gate.py --receipt path/to/receipt.json --evidence path/to/audited_evidence.json`

Exit code 0 means **supplied evidence passes screening**, not independent authentication. Exit code 2 means missing/invalid evidence. The original 16 synthetic tests and run output remain in the local cycle bundle.

## Next
Get vendor-matched historical closes with first-publication evidence, validate complete observed-close sequence and source vintage independently, then compute descriptive error. Avoid interpreting the h1 persistence model as an improvement over its identical baseline.
