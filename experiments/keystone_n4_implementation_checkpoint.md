# Keystone n=4 exact dependence implementation checkpoint

The current `tools/dependence_bounds.py` is still capped at n<=3 when pairwise constraints are present. Prior exact benchmarking established that n=4 is tractable for the existing dependency-free vertex enumerator: 16 worlds and at most C(16,8)=12,870 candidate bases; with all six pairwise constraints there are C(16,11)=4,368 bases.

## Intended minimal implementation

1. Change the pairwise-constrained cap from `n > 3` to `n > 4`.
2. Update docstrings from n<=3 to n<=4.
3. Add this regression target:

```python
pairs4={(i,j):.25 for i in range(4) for j in range(i+1,4)}
lo,hi=all_fail_bounds([.5]*4,pairs4)
assert abs(lo-0.0)<1e-9
assert abs(hi-(1.0/6.0))<1e-9
```

This captures the key fact that pairwise independence does not imply mutual independence: P(all four fail) can range from 0 to 1/6 rather than being fixed at 1/16.

## Boundary

Do not extend the same enumerator to n=5. With 32 worlds and normalization + 5 marginals + 10 pairwise equalities, the fully constrained case can require C(32,16)=601,080,390 candidate bases. n>=5 needs a different LP architecture.

## Tooling status

A direct contents-API replacement of `tools/dependence_bounds.py` was attempted after fetching its current blob SHA, but the write was blocked before execution by the platform safety layer. No implementation change should be claimed until a repository write is confirmed.
