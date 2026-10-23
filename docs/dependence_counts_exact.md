# Exact-count dependence bounds (experimental, opt-in)

`tools.dependence_counts_exact` computes tight bounds on the probability
that **all** specified binary failure modes fail, or that **at least one**
survives. It accepts integer counts rather than floating-point probabilities
and returns exact `fractions.Fraction` values.

## Example

```python
from fractions import Fraction
from tools.dependence_counts_exact import (
    all_fail_bounds_from_counts,
    any_survives_bounds_from_counts,
)

# Among the SAME 10 observations, A fails 5 times, B fails 5 times,
# and A and B fail together twice.
assert all_fail_bounds_from_counts(10, [5, 5], {(0, 1): 2}) == (
    Fraction(1, 5), Fraction(1, 5))
assert any_survives_bounds_from_counts(10, [5, 5], {(0, 1): 2}) == (
    Fraction(4, 5), Fraction(4, 5))

# Missing joint observations yield an interval, not an independence estimate.
assert all_fail_bounds_from_counts(10, [5, 5]) == (
    Fraction(0), Fraction(1, 2))
```

## Input contract

- `total` is a positive integer number of observations.
- `marginal_counts[i]` is the number of observations where mode `i` fails.
- `pairwise_counts[(i, j)]` is the number where **both** fail; keys must
  be zero-based integer pairs with `0 <= i < j < len(marginal_counts)`.
- All supplied counts must refer to the **same population**, with consistent
  binary definitions and no missing observations. Do not mix cohorts,
  conditional rates, percentages, or rounded probabilities.
- A missing pairwise key means *unknown*, not zero.

## Scope and interpretation

Each connected component of the supplied pairwise-constraint graph may be
an isolated mode, a tree, or a complete three-mode triangle. Multiple such
components can coexist (e.g., a triangle plus an edge or two triangles).
Larger cyclic components and triangles with attached edges are **not**
implemented and raise `NotImplementedError`. Invalid counts and
mathematically inconsistent supported constraints raise `ValueError`.

Bounds are tight over all joint binary distributions compatible with the
specified counts. They do **not** assume independence, estimate uncertainty
from finite samples, or validate that counts were measured correctly.
The exact-count API does not replace `tools.dependence_bounds` for callers
that have only floating-point probabilities.

Run the dependency-free tests with:

```sh
python -m unittest discover -s tests -p 'test_dependence_counts_exact.py' -v
```
