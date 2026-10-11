# Keystone — subset Bonferroni hierarchy for heterogeneous joint-failure risk (2026-10-11)

## Motivation
Previous lab research showed that averaging heterogeneous failure moments can grossly overestimate the sharp joint-failure bound. This note supplies a **cheap certified upper bound that uses every individual marginal and pairwise intersection**, without requiring a full 2^n-atom linear program. It is **not generally sharp**.

## Theorem (exact arithmetic)
For events E_1,...,E_n, let p_i=P(E_i) and q_ij=P(E_i ∩ E_j). For any nonempty subset S, define F_i=E_i^c. The second-order Bonferroni inequality gives

P(∪_{i∈S} F_i) ≥ Σ_{i∈S} (1-p_i) − Σ_{i<j∈S} (1-p_i-p_j+q_ij).

Since ∩_{i=1}^n E_i ⊆ ∩_{i∈S} E_i, it follows that

**P(∩_{i=1}^n E_i) ≤ U_S := 1 − Σ_{i∈S}(1-p_i) + Σ_{i<j∈S}(1-p_i-p_j+q_ij).**

Therefore U* = min_{∅≠S⊆[n]} U_S is a certified upper bound. A subset of size one gives p_i; size two gives q_ij; size three gives the three-event Bonferroni cap. Searching larger subsets can be strictly stronger. This is a valid bound for arbitrary dependence; it does **not** assume pairwise independence.

## Exact four-event separation
Choose exactly one of four systems to succeed, uniformly, and let the other three fail. Then p_i=3/4 and q_ij=1/2 for every i≠j. For every triple S, U_S=1/4. Yet with S={1,2,3,4}, U_S=0, so P(all four fail)=0 **is forced by pairwise moments alone**. This is also confirmed by a full-atom LP maximizing P(1111). Thus all one-, two-, and three-event caps can miss a sharp zero upper bound.

More generally, when exactly one of n≥4 events is absent, chosen uniformly, p_i=1−1/n and q_ij=1−2/n. Full-set U_[n]=0, whereas any proper subset S of size k has U_S=1−k/n. This demonstrates a strict hierarchy even for fully symmetric moments.

## Verification
A local Python implementation uses fractions.Fraction to avoid certification errors from floating-point inputs. Three unittest methods passed, including 140 seeded random feasible distributions (35 each for n=3,4,5,6). In every random case, the subset cap was ≥ the full-atom SciPy HiGHS LP optimum (within 1e-8) and ≤ the best size≤3 cap. The explicit four-event example yielded U_≤3=1/4, U_≤4=0, LP optimum=0. This is verification, not a proof of general LP sharpness.

## Limitations and next steps
Enumerating all subsets costs O(2^n n^2) naively, still often cheaper than solving a 2^n-atom LP but not scalable to thousands of events. Subset caps can be loose and elementary pairwise feasibility checks are not sufficient for joint feasibility. For large n, use limited subset sizes, heuristic search, or structure-aware relaxations, always retaining the validity of each selected U_S. Compare with exact LP for small n before using operationally. No empirical agent failure rates were measured in this study.
