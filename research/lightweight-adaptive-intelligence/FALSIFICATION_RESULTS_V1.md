# Falsification Results v1 — post disjoint-input fix

Date: 2026-10-06
Benchmark commit before this report: a1386549260c3fea98fae2780d4c05f334da38be
Protocol: 100 deterministic episodes per family (300 total), seed0=20261005, 6 train + 12 test-A + 12 test-B per episode.

## Verified aggregate accuracy (A+B semantic controls combined)

| Family | Retrieval | FamilyOracle | HintFreeMDL |
|---|---:|---:|---:|
| affine | 0.0000 | 1.0000 | 1.0000 |
| permutation | 0.0000 | 1.0000 | 1.0000 |
| value_conditional | 0.0000 | 0.9954167 | 0.0054167 |

For value_conditional, 99/100 training sets observed both parities. Restricted to those identifiable episodes:
- FamilyOracle: 1.0000
- HintFreeMDL: 0.0000

The single remaining oracle loss is therefore an identifiability issue (one parity absent from six training examples), not evidence of generator leakage or oracle failure.

## Conclusions

1. The disjoint-input invariant works: retrieval is exactly zero across all three families.
2. The fixed HintFreeMDL grammar solves affine and fixed permutation perfectly but fails on value-conditional composition when the necessary evidence is present.
3. The benchmark now contains a clean capability gap suitable for the next experiment: discover conditional/compositional rules without receiving the family label.
4. Do not treat representation-B semantic control as proof of text-level representation transfer; semantic tuples are still supplied to systems.

## Next experiment

Implement a hint-free grammar-expansion learner that can propose a shallow conditional split over observable input predicates (starting with parity of sum) and fit a separate permutation under each branch. Evaluate with an explicit complexity penalty against the fixed-rule MDL baseline. The purpose is not to hard-code the benchmark answer as a final learner, but to test whether controlled grammar expansion closes the identified capability gap without regressing the simpler families.
