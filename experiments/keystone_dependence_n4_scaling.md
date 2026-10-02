# Dependence bounds scaling note: n=4 is tractable, n=5 is not

Keystone checkpoint.

The current `tools/dependence_bounds.py` uses exact basic-feasible-vertex enumeration for pairwise-constrained binary failure systems and caps that path at n<=3.

For n=4 there are 16 binary worlds. The equality system has:
- 1 normalization constraint,
- 4 marginal constraints,
- between 1 and 6 selected pairwise constraints.

Therefore the number of candidate bases is C(16,m), where m is between 6 and 11. Across that range the maximum is C(16,8)=12,870; with all six pairwise constraints it is C(16,11)=4,368. This is small enough to make n=4 a reasonable exact extension with a runtime regression guard.

For n=5 there are 32 worlds. With all marginals and all 10 pairwise constraints, m=16 and the naive enumerator would face C(32,16)=601,080,390 candidate bases. So simply changing the cap to n<=5 would be unjustified.

A useful exact regression case for n=4 is four Bernoulli failure events with marginals 1/2 and every pairwise intersection 1/4. Pairwise independence does not imply mutual independence; the exact feasible range is:

    0 <= P(all four fail) <= 1/6

whereas full independence would select 1/16.

Recommended implementation direction:
1. extend the current exact enumerator to n=4 only;
2. add the four-event pairwise-independent regression case;
3. add a runtime guard/benchmark;
4. keep n>=5 rejected on the vertex-enumeration path until a proper LP solver or a more specialized method replaces it.

This note records analysis only; it does not claim that `tools/dependence_bounds.py` has been modified.
