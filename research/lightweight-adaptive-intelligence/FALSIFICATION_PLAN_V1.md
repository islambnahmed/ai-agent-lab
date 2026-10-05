# Benchmark v1 falsification plan

This checkpoint freezes the next checks before tuning the hint-free learner.

## Known corrections
- The former sequence family was reducible to a fixed permutation and has been replaced by value_conditional.
- acc_B_semantic_control is not cross-representation transfer because the executable harness still supplies semantic tuples to predictors.

## Required checks
1. FamilyOracle should remain strong on affine, permutation, and value_conditional episodes.
2. HintFreeMDL should solve ordinary permutation episodes but fail value_conditional episodes, demonstrating that the new family lies outside its fixed-permutation grammar.
3. Retrieval should fail to generalize to held-out inputs except accidental collisions.
4. Report value_conditional episodes where training contains only one parity separately; the oracle deliberately leaves unseen parity undefined.
5. Do not claim representation transfer until predictors consume surface representation directly.

## Representation-B design
A later valid test should distinguish:
- Grounded-B: changed surface encoding plus task-agnostic grounding sufficient to interpret symbols, with no family/operator hint.
- Ungrounded-B: fresh arbitrary symbols without grounding, used as an impossible/leakage control. Above-chance performance here is suspicious.

## Decision rule
Do not tune or extend HintFreeMDL until checks 1-4 are measured on deterministic multi-seed runs. If the oracle is weak because training omitted a parity, stratify or rebalance episode generation before comparing learners.
