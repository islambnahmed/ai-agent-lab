# Experiment 17 — Exact three-event bounds

## Question
For three events A, B, C, when all three marginals and all three pairwise intersections are known, can feasibility and the possible triple intersection be characterized directly rather than delegated to a floating-point LP solver?

## Derivation
Let:
- a=P(A), b=P(B), c=P(C)
- ab=P(A∩B), ac=P(A∩C), bc=P(B∩C)
- t=P(A∩B∩C)

The eight atomic probabilities imply these lower bounds on t:

- t >= 0
- t >= ab + ac - a
- t >= ab + bc - b
- t >= ac + bc - c

and these upper bounds:

- t <= ab
- t <= ac
- t <= bc
- t <= 1 - a - b - c + ab + ac + bc

Therefore:

L = max(0, ab+ac-a, ab+bc-b, ac+bc-c)
U = min(ab, ac, bc, 1-a-b-c+ab+ac+bc)

The supplied constraints are jointly feasible iff L <= U, subject to ordinary probability-domain validation.

## Independent verification
The direct formula was compared against an exact rational oracle over 1,000 generated feasible distributions. Observed mismatches: 0/1000.

This is evidence for the formula on the tested domain, not a proof supplied by the randomized test itself; the algebra above provides the structural derivation.

## Counterexample: pairwise-valid but globally impossible
Take:

- P(A)=0.67
- P(B)=0.70
- P(C)=0.58
- P(A∩B)=0.62
- P(A∩C)=0.38
- P(B∩C)=0.32

Each pairwise intersection individually satisfies its two-event Frechet bounds.

But globally:

L = max(0, 0.62+0.38-0.67, 0.62+0.32-0.70, 0.38+0.32-0.58)
  = max(0, 0.33, 0.24, 0.12)
  = 0.33

U = min(0.62, 0.38, 0.32, 1-0.67-0.70-0.58+0.62+0.38+0.32)
  = min(0.62, 0.38, 0.32, 0.37)
  = 0.32

Since L > U, no joint distribution exists.

## Reusable lesson
Local consistency of every pair does not imply global consistency of the full constraint system. When a low-dimensional exact characterization is available, use it as a pre-solver oracle: it avoids floating-point feasibility ambiguity and provides an independently checkable explanation for rejection.

## Scope
This exact shortcut is specifically for the three-event case with complete marginal and pairwise information. It should not be generalized to arbitrary partial constraints or larger dependency systems without a new derivation and independent tests.
