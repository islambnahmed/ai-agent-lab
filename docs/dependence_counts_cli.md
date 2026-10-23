# Offline exact-count CLI (experimental)

A reproducible, **opt-in local caller** for the exact-count solver. It reads a JSON file (or standard input), performs no network requests, and prints one JSON result containing rational bounds. It does not change the existing floating-probability API or deploy anything.

## Example

Save as `example.json`:

```json
{
  "total": 10,
  "marginal_counts": [5, 5],
  "pairwise_counts": [{"i": 0, "j": 1, "count": 2}]
}
```

From the repository root:

```sh
python -m tools.dependence_counts_cli example.json
# or: cat example.json | python -m tools.dependence_counts_cli -
python -m unittest discover -s tests -p 'test_dependence_counts_cli.py' -v
```

The result includes `"all_fail":{"lower":"1/5","upper":"1/5"}`, `"any_survives":{"lower":"4/5","upper":"4/5"}`, input counts summary, and `input_sha256`. Bounds are **exact fraction strings**; the hash identifies the raw input bytes for reproducibility, not the data's empirical validity. The output `total` is a **decimal string** (for example `"total":"9007199254740993"`), never a JSON number, because JavaScript JSON parsers round integer values above `2^53 - 1`. `mode_count` and `pairwise_constraint_count` remain bounded JSON numbers. Input `total` and counts must still be JSON integers; this output representation does not change the input contract.

## Contract

- `total` is a positive JSON integer, the size of **one shared population**.
- `marginal_counts` is a nonempty array of integer failure counts in that population.
- `pairwise_counts` is an array of objects with exactly `i`, `j`, and `count`; `0 <= i < j < len(marginal_counts)`. The count is the number of observations where **both** specified modes fail.
- Missing pairs are **unknown**, not zero. All counts must use the same observation universe and binary failure definitions; percentages, rates, different cohorts, or rounded probabilities are invalid inputs.
- Duplicate JSON keys, duplicate pairwise edges, booleans masquerading as integers, unexpected fields, malformed JSON, and inconsistent constraints are rejected with exit code 2.
- Input size is capped at 2,000,000 bytes, mode count at 4,096, and pairwise entries at 8,192. These are local CLI resource guards, not mathematical restrictions of the underlying API.
- A supported constraint graph consists of isolated vertices, trees, and/or complete 3-node triangles, including disconnected combinations. Other cycles are rejected with exit code 2.
- No uncertainty estimates, statistical confidence intervals, or evidence of shared-population provenance are supplied. The tool bounds feasible joint binary distributions; it does **not** predict future outcomes.

For mathematical scope, see [Exact-count dependence bounds](dependence_counts_exact.md).

## Status

This is an experimental offline interface and a concrete example caller for the opt-in solver. Its availability does not imply deployment or readiness for production ingestion. Review data provenance and operational requirements before merging PR #6.
